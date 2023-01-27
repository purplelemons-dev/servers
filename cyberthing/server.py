
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord

HOST, PORT = "0.0.0.0", 10001

class Handler(BaseHTTPRequestHandler):

    def send_bot_message(self, message: str):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(message.encode())

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(404)
            self.end_headers()
            return
        if self.path != "/":
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()
            return
        try:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            with open("./public/index.html", "rb") as f:
                self.wfile.write(f.read())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())


# TODO resolve POST request to discord bot

server = HTTPServer((HOST, PORT), Handler)

if __name__ == "__main__":
    print(f"Server started on http://127.0.0.1:{PORT}")
    server.serve_forever()
