
from http.server import HTTPServer, SimpleHTTPRequestHandler
PORT = 666

server = HTTPServer(('0.0.0.0', PORT), SimpleHTTPRequestHandler)
server.serve_forever()
