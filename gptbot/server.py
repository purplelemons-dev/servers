from http.server import BaseHTTPRequestHandler, HTTPServer
from http.cookies import SimpleCookie
from conversations import Conversations, shared_resource
from threading import Thread
from urllib.parse import urlparse, parse_qs
from random import getrandbits as grb
from base64 import b64encode
import json
from time import sleep
import requests
from traceback import print_exc
from hashlib import sha256

# TODO: verify that the user is in the server
# TODO: /api/remove - gets rid of a user
# TODO: bot gets a token

post_endpoints = ("/generate", "/conversation")
get_endpoints = ("/", "/login", "/logout")


def oauth_url(state):
    return f"https://discord.com/oauth2/authorize?response_type=token&client_id=1086501141594001429&state={get_hash(state)}&scope=identify%20guilds"


def get_hash(s: str):
    return sha256(s.encode("utf8")).hexdigest()


class Attrs:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class Session:
    def __init__(self, access_token: str = None, user_id: int = None):
        self.access_token: str = access_token
        self.user_id: int = user_id
        self.resolved: bool = False

    def __str__(self):
        return f"Session(access_token={self.access_token},user_id={self.user_id},resolved={self.resolved})"

    def __repr__(self):
        return str(self)

    @property
    def __dict__(self):
        """
        Returns a JSON-serializable dictionary.
        """
        return {
            "access_token": self.access_token,
            "user_id": self.user_id,
            "resolved": self.resolved,
        }


try:
    with open("sessions.json", "r") as f:
        sessions: dict[str, dict[str, str]] = json.load(f)
        for key, value in sessions.items():
            sessions[key] = Session(**value)
except FileNotFoundError:
    sessions = {}


class GPTBotHandler(BaseHTTPRequestHandler):
    resource: shared_resource
    sessions: dict[str, Session] = sessions
    body: dict[str,]

    def on_request(self):
        readable = int(self.headers.get("Content-Length", 0))
        if readable:
            self.body = json.loads(self.rfile.read(readable))
        else:
            self.body = {}

    @property
    def authorization(self) -> str:
        """
        Returns the authorization header. If it does not exist, returns None.
        """
        auth = self.headers.get("Authorization")
        return auth.split(" ")[-1] if auth else None

    def do_GET(self):
        self.on_request()
        # send user to / if they are not logged in
        parsed = urlparse(self.path)
        self.path = parsed.path
        self.query = parse_qs(parsed.query)

        # if the user is trying to login
        if self.path == "/login":
            print("got login request")
            # generate a random session token and hash it
            sess_token = b64encode(str(grb(128)).encode("utf8")).decode("utf8")
            # store the session token in the sessions dictionary
            self.sessions[sess_token] = Session()
            self.send_response(302)
            self.send_header(
                "Location",
                oauth_url(
                    sess_token
                ),  # redirect to discord oauth with hashed sess_token (state)
            )
            # set/override the session cookie. they may have been sent here b/c CSRF
            self.send_header("Set-Cookie", f"sess_token={sess_token}")
            self.end_headers()
            return

        if self.path == "/api/conversation":
            if self.sessions[self.authorization].resolved:
                # return a list of {"role": "type", "content": "text"} found in resource
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"message": "success"}
                uid = int(self.sessions[self.authorization].user_id)
                try:
                    conversation = self.resource.conversations[uid]
                except KeyError:
                    #print("no conversation found")
                    conversation = []
                response["conversation"] = conversation
                try:
                    system = self.resource.conversations.system_messages[uid]
                except KeyError:
                    #print("no system messages found")
                    system = []
                response["system"] = system
                self.wfile.write(json.dumps(response).encode("utf8"))
                return

            else:
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                message = {
                    "message": "unauthorized, try POST /api/validate with your access token, state, and session token"
                }
                self.wfile.write(json.dumps(message).encode("utf8"))
                return

        if self.path == "/api/generate":
            cookies = SimpleCookie(self.headers.get("Cookie"))
            try:
                sess_token = cookies["sess_token"].value
            except KeyError:
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                message = {
                    "message": "unauthorized, try POST /api/validate with your access token, state, and session token"
                }
                self.wfile.write(json.dumps(message).encode("utf8"))
                return
            # we have a valid session
            if self.sessions[sess_token].resolved:
                self.send_response(200)
                self.send_header("Content-type", "text/event-stream")
                self.end_headers()
                full_message, uid = "", int(self.sessions[sess_token].user_id)
                member = Attrs(id=uid)
                print(f"sending...")
                for message in self.resource.conversations.next_prompt_stream(member):
                    # print(message)
                    if message.choices[0].finish_reason is not None:
                        self.wfile.write(b"event: finish\n")
                        self.wfile.write(b"data: ")
                        self.wfile.write(
                            json.dumps({ "reason": message.choices[0].finish_reason }).encode("utf8")
                        )
                        self.wfile.write(b"\n\n")
                        self.wfile.flush()

                        print(f"full_message: {full_message}")
                        self.resource.conversations.add_history(
                            member,
                            "assistant",
                            full_message
                        )
                        return
                    delta = message.choices[0].delta
                    if "content" in delta:
                        content: str = delta["content"]
                        full_message += content
                        # Send data: line
                        self.wfile.write(b"data: ")
                        self.wfile.write(
                            json.dumps({"content": content}).encode("utf8")
                        )
                        # 2x newline
                        self.wfile.write(b"\n\n")
                        self.wfile.flush()
                return
            else:
                # we are not logged in
                self.send_response(403)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                message = {"message": f"403 Forbidden: Not logged in\n"}
                self.wfile.write(json.dumps(message).encode("utf8"))
                return


        if self.path == "/api/test":
            cookies = SimpleCookie(self.headers.get("Cookie"))
            print(cookies)
            self.send_response(200)
            self.send_header("Content-type", "text/event-stream")
            self.end_headers()
            while 1:
                self.wfile.write(b"data: hello\n\n")
                self.wfile.flush()
                sleep(1)
            return

        try:
            with open("public" + self.path, "rb") as f:
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
            with open("public" + self.path, "rb") as f:
                doc = f.read()

        ext = self.path.split(".")[-1]
        self.send_response(200)
        self.send_header(
            "Content-type",
            {"html": "text/html", "css": "text/css", "js": "application/javascript"}[
                ext
            ],
        )
        self.end_headers()
        self.wfile.write(doc)

    def do_POST(self):
        self.on_request()
        parsed = urlparse(self.path)
        self.path = parsed.path
        self.query = parse_qs(parsed.query)
        if self.path == "/api/validate":
            # debug print(f"Validating session {self.body}")
            # The user has sent a json body of {state: str, access_token: str}
            # where state is something we generated and access_token is the discord token
            # we need to validate the state and then store the access_token
            if "state" in self.body and "access_token" in self.body:
                state: str = self.body["state"]
                access_token: str = self.body["access_token"]
                if self.authorization is not None:
                    if sha256(self.authorization.encode("utf8")).hexdigest() != state:
                        # invalid state
                        self.send_response(401)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        message = {"message": "unauthorized"}
                        self.wfile.write(json.dumps(message).encode("utf8"))
                        return
                    if self.authorization in self.sessions:
                        # Try to login to discord
                        r_identify = requests.get(
                            "https://discord.com/api/users/@me",
                            headers={"Authorization": f"Bearer {access_token}"},
                        )
                        if r_identify.status_code == 200:
                            # we are logged in
                            # self.sessions[state].access_token = access_token
                            discord_user = r_identify.json()
                            # debug print(f"sessions looks like {self.sessions=}")
                            self.sessions[self.authorization].user_id = discord_user[
                                "id"
                            ]
                            r_guilds = requests.get(
                                "https://discord.com/api/users/@me/guilds",
                                headers={"Authorization": f"Bearer {access_token}"},
                            )
                            if r_guilds.status_code == 200:
                                # we have guilds
                                for guild in r_guilds.json():
                                    if guild["id"] == "1087082509621272767":
                                        # we are in the server
                                        # debug print(f"We are in the server\n{self.sessions=}")
                                        self.sessions[
                                            self.authorization
                                        ].resolved = True
                                        self.sessions[
                                            self.authorization
                                        ].access_token = access_token
                                        self.send_response(200)
                                        self.send_header(
                                            "Content-type", "application/json"
                                        )
                                        self.end_headers()
                                        message = {
                                            "message": "success",
                                            # user_id is used by the client script to get conversations
                                            "user_id": self.sessions[
                                                self.authorization
                                            ].user_id,
                                            # fullname is used by the client script to display the user's name on login
                                            "fullname": discord_user["username"]
                                            + "#"
                                            + discord_user["discriminator"],
                                        }
                                        # add to sessions
                                        self.wfile.write(
                                            json.dumps(message).encode("utf8")
                                        )
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
                                message = {
                                    "message": f"{r_guilds.status_code} Discord token invalid\n"
                                }
                                self.wfile.write(json.dumps(message).encode("utf8"))
                            return
                        return
                    else:
                        # state is not valid
                        self.send_response(401)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        message = {
                            "message": f"401 Unauthorized: Requires valid authorization header\n"
                        }
                        self.wfile.write(json.dumps(message).encode("utf8"))
                        return
            else:
                # no state or access_token
                self.send_response(401)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                message = {
                    "message": f"401 Unauthorized: no authorization header\n"
                }
                self.wfile.write(json.dumps(message).encode("utf8"))
                return
        
        elif self.path == "/api/update":
            if self.authorization is not None:
                if self.authorization in self.sessions:
                    uid=int(self.sessions[self.authorization].user_id)
                    self.resource.conversations.system_messages[uid] = self.body["system"]
                    self.resource.conversations.add_history(
                        Attrs(id=uid),
                        "user",
                        self.body["content"]
                    )
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    message = {"message": "success"}
                    self.wfile.write(json.dumps(message).encode("utf8"))
                    return
                else:
                    self.send_response(401)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    message = {
                        "message": f"401 Unauthorized: Requires valid authorization header\n"
                    }
                    self.wfile.write(json.dumps(message).encode("utf8"))
                    return

def run(resource: shared_resource, port=10002):
    print("starting server...")
    server_address = ("0.0.0.0", port)
    handler = GPTBotHandler
    handler.resource = resource
    httpd = HTTPServer(server_address, handler)
    print("running server...")
    serve_forever = Thread(target=httpd.serve_forever)
    serve_forever.start()
    while resource.running:
        sleep(1)
    # shut down
    serve_forever.join()
    print("shutting down http server...")
    httpd.shutdown()
    httpd.server_close()
    # save sessions
    print("saving sessions...")
    with open("sessions.json", "w") as f:
        json.dump(handler.sessions, f, default=lambda o: o.__dict__)


if __name__ == "__main__":
    run(Conversations(), port=1111)
