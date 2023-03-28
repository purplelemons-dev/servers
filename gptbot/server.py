
from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from conversations import Conversations, shared_resource
from urllib.parse import urlparse, parse_qs
from random import getrandbits as grb
from base64 import b64encode
import json
from dataclasses import dataclass
import requests
from hashlib import sha256

# TODO: save sessions to json
# TODO: verify that the user is in the server
# TODO: /api/remove - gets rid of a user 
# TODO: bot gets a token

post_endpoints =("/generate","/conversation")
get_endpoints = ("/","/login","/logout")

def oauth_url(state): return f"https://discord.com/oauth2/authorize?response_type=token&client_id=1086501141594001429&state={get_hash(state)}&scope=identify%20guilds"

def get_hash(s:str): return sha256(s.encode("utf8")).hexdigest()

class Attrs:
    def __init__(self,**kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)

class Session:
    def __init__(self,access_token:str,user_id:int):
        self.access_token:str = access_token
        self.user_id:int = user_id
        self.resolved:bool = False
    
    @property
    def __dict__(self):
        """
        Returns a JSON-serializable dictionary.
        """
        return {
            "access_token": self.access_token,
            "user_id": self.user_id,
            "resolved": self.resolved
        }

try:
    with open("sessions.json","r") as f:
        sessions:dict[str,dict[str,str]] = json.load(f)
        for key,value in sessions.items():
            sessions[key] = Session(**value)
except FileNotFoundError:
    sessions = {}

class GPTBotHandler(BaseHTTPRequestHandler):

    resource:shared_resource
    sessions:dict[str,Session] = sessions

    @property
    def body(self) -> dict[str,]:
        return json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8"))

    def do_GET(self):
        # send user to / if they are not logged in
        parsed = urlparse(self.path)
        self.path = parsed.path
        self.query = parse_qs(parsed.query)

        cookies = SimpleCookie(self.headers.get("Cookie"))
        if "session" in cookies: # we check for session token validity first, then authorization bearer
            session = cookies["session"].value
            if session in self.sessions:
                if not self.sessions[session].resolved:
                    # they created a session but didn't validate it via discord. we need to create a new session
                    del self.sessions[session]
                    self.send_response(302)
                    self.send_header("Location", "/login")
                    self.send_header("Set-Cookie", "sess_token=; Max-Age=0; Path=/")
                    self.end_headers()
                    return
                else:
                    # we're good!
                    pass
            else:
                # session exists but is not in sessions
                self.send_response(302)
                self.send_header("Location", "/login")
                self.send_header("Set-Cookie", "sess_token=; Max-Age=0; Path=/")
                self.end_headers()
                return
        else: # no session, so we try authorization bearer
            authorization: str = self.headers.get("Authorization")
            if authorization:
                auth_token = authorization.split("Bearer ")[1]
                if auth_token in self.sessions:
                    if not self.sessions[auth_token].resolved:
                        del self.sessions[auth_token]
                        self.send_response(401)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        message = {
                            "message": "unauthorized"
                        }
                        self.wfile.write(json.dumps(message).encode("utf8"))
                        return
                    else:
                        pass # we're good!
                else:
                    # auth token exists but is not in sessions
                    self.send_response(401)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    message = {
                        "message": "unauthorized"
                    }
                    self.wfile.write(json.dumps(message).encode("utf8"))
                    return
            else:
                # no session or auth token
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return

        # if the user is trying to login
        if self.path=="/login":
            # generate a random session token and hash it
            sess_token = b64encode(str(grb(128)).encode("utf8")).decode("utf8")
            # store the session token in the sessions dictionary
            self.sessions[sess_token] = Session()
            self.send_response(302)
            self.send_header(
                "Location",
                oauth_url(sess_token) # redirect to discord oauth with hashed sess_token (state)
            )
            self.send_header("Set-Cookie", f"sess_token={sess_token}")
            self.end_headers()
            return
        try:
            with open("public"+self.path,"rb") as f:
                doc = f.read()
        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            message = "404 Not Found\n"
            self.wfile.write(message.encode("utf8"))
            return
        except IsADirectoryError:
            self.path = "/index.html"
            with open("public"+self.path,"rb") as f:
                doc = f.read()
        
        ext = self.path.split(".")[-1]
        self.send_response(200)
        self.send_header("Content-type", {
            "html": "text/html",
            "css": "text/css",
            "js": "application/javascript"
        }[ext])
        self.end_headers()
        self.wfile.write(doc)

    def do_POST(self):
        parsed = urlparse(self.path)
        self.path = parsed.path
        self.query = parse_qs(parsed.query)
        if self.path == "/api/validate":
            # The user has sent a json body of {state: str, access_token: str}
            # where state is something we generated and access_token is the discord token
            # we need to validate the state and then store the access_token
            if "session" in self.body and "access_token" in self.body:
                session:str = self.body["session"]
                access_token:str = self.body["access_token"]
                if session in self.sessions:
                    # Try to login to discord
                    r_identify = requests.get("https://discord.com/api/users/@me",headers={"Authorization":f"Bearer {access_token}"})
                    if r_identify.status_code == 200:
                        # we are logged in
                        #self.sessions[state].access_token = access_token
                        discord_user = r_identify.json()
                        self.sessions[session].user_id = discord_user["id"]
                        r_guilds = requests.get("https://discord.com/api/users/@me/guilds",headers={"Authorization":f"Bearer {access_token}"})
                        if r_guilds.status_code == 200:
                            # we have guilds
                            for guild in r_guilds.json():
                                if guild["id"] == "1087082509621272767":
                                    # we are in the server
                                    self.sessions[session].resolved = True
                                    self.sessions[session].access_token = access_token
                                    self.send_response(200)
                                    self.send_header("Content-type", "application/json")
                                    self.end_headers()
                                    message = {
                                        "message": "success",
                                        # user_id is used by the client script to get conversations
                                        "user_id": self.sessions[session].user_id,
                                        # fullname is used by the client script to display the user's name on login
                                        "fullname": discord_user["username"]+"#"+discord_user["discriminator"]
                                    }
                                    # add to sessions
                                    self.wfile.write(json.dumps(message).encode("utf8"))
                                    return
                            # we are not in the server
                            self.send_response(403)
                            self.send_header("Content-type", "application/json")
                            self.end_headers()
                            message = {"message": f"403 Forbidden: Not in server\n"}
                            self.wfile.write(json.dumps(message).encode("utf8"))
                        else:
                            # we don't have guilds
                            self.send_response(r_guilds.status_code)
                            self.send_header("Content-type", "application/json")
                            self.end_headers()
                            message = {"message": f"{r_guilds.status_code} Discord token invalid\n"}
                            self.wfile.write(json.dumps(message).encode("utf8"))
                        return
                    return
                else:
                    # state is not valid
                    self.send_response(403)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    message = {"message": f"403 Forbidden: Invalid state\n"}
                    self.wfile.write(json.dumps(message).encode("utf8"))
                    return

def run(resource:shared_resource, port=10002):
    print("starting server...")
    server_address = ("0.0.0.0", port)
    handler = GPTBotHandler
    handler.resource = resource
    httpd = HTTPServer(server_address, GPTBotHandler)
    print("running server...")
    while handler.resource.running:
        # This thread may take a while to exit because each new request is blocking
        httpd.handle_request()
    # shut down   
    print("shutting down http server...")
    httpd.shutdown()
    httpd.server_close()
    # save sessions
    print("saving sessions...")
    with open("sessions.json","w") as f:
        json.dump(handler.sessions,f,default=lambda o: o.__dict__)

if __name__ == "__main__":
    conversations = Conversations()
    run(conversations,port=1111)
