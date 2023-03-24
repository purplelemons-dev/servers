
from http.server import BaseHTTPRequestHandler, HTTPServer
from conversations import Conversations

class GPTBotHandler(BaseHTTPRequestHandler):

    conversations:Conversations

    def do_GET(self):
        if self.path!= "/":
            self.send_header("Location", "/")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = "Hello World! from gpt server\n"
        self.wfile.write(message.encode("utf8"))

    def do_POST(self):
        base = "/api/v1"
        endpoints =("/next_prompt",)
        if self.path.startswith(base):
            endpoint = self.path[len(base):]
            if endpoint in endpoints:
                if endpoint == "/next_prompt":
                    self.next_prompt()
                    return
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        message = "404 Not Found\n"
        self.wfile.write(message.encode("utf8"))

def run(conversations:Conversations):
    try:
        print('starting server...')
        server_address = ('0.0.0.0', 10002)
        handler = GPTBotHandler
        handler.conversations = conversations
        httpd = HTTPServer(server_address, handler)
        print('running server...')
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('^C received, shutting down the web server')
        httpd.shutdown()
        httpd.server_close()
