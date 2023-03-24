
from http.server import BaseHTTPRequestHandler, HTTPServer
from conversations import Conversations
from urllib.parse import urlparse
import json

post_endpoints =("/generate","/conversation")
get_endpoints = ("/","/login","/logout")

class Attrs:
    def __init__(self,**kwargs):
        for key,value in kwargs.items():
            setattr(self,key,value)

class GPTBotHandler(BaseHTTPRequestHandler):

    conversations:Conversations

    def do_GET(self):
        # send user to / if they are not logged in
        parsed = urlparse(self.path)
        try:
            with open(self.path[1:],"rb",encoding="utf-8") as f:
                doc = f.read()
        except FileNotFoundError:
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            message = "404 Not Found\n"
            self.wfile.write(message.encode("utf8"))
            return
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
        global post_base, post_endpoints
        if self.path.startswith(post_base):
            endpoint = self.path[len(post_base):]
            if endpoint in post_endpoints:
                if endpoint == "/generate":
                    # json body
                    body:dict[str,] = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8"))
                    user_id = int(body["user_id"])
                    response = self.conversations.next_prompt(Attrs(id=user_id))
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "success",
                        "errors": [],
                        "data": {
                            "response": response
                        }
                    }).encode("utf8"))
                    return
                elif endpoint == "/conversation":
                    # json body
                    body:dict[str,] = json.loads(self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8"))
                    user_id = int(body["user_id"])
                    
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "message": "success",
                        "errors": [],
                        "data": {
                            "response": response
                        }
                    }).encode("utf8"))
                    return
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = "404 Not Found\n"
        self.wfile.write(message.encode("utf8"))

def run(conversations:Conversations,port=10002):
    try:
        print('starting server...')
        server_address = ('0.0.0.0', port)
        handler = GPTBotHandler
        handler.conversations = conversations
        httpd = HTTPServer(server_address, handler)
        print('running server...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
        httpd.shutdown()
        httpd.server_close()

if __name__ == "__main__":
    conversations = Conversations()
    run(conversations,port=1111)
