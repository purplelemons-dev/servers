
from http.server import HTTPServer, BaseHTTPRequestHandler
import discord
from json import loads

HOST="0.0.0.0"
PORT=10001

def create_server(bot:discord.Client):

    class Handler(BaseHTTPRequestHandler):

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

        def do_POST(self):
            if self.path == "/botaction":
                content_length = int(self.headers["Content-Length"])
                body:dict[str,] = loads(self.rfile.read(content_length))
                try:
                    bot.message_queue.append(body["message"])
                except KeyError:
                    self.send_response(400)
                    self.end_headers()
                    self.wfile.write(b"Missing 'message' key in body")
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(str(e).encode())
                else:
                    self.send_response(200)
                    self.end_headers()
                return
            self.send_response(404)
            self.end_headers()

    return HTTPServer((HOST, PORT), Handler)

if __name__ == "__main__":
    print(f"Server started on http://127.0.0.1:{PORT}")
    #create_server().serve_forever()
