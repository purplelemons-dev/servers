#!/usr/bin/env python
#
# Created by Josh Smith
# Mon 19 Sep 2022 08:21:04 PM CDT
#

import requests
import http.server
PORT = 5005

class Server(http.server.BaseHTTPRequestHandler):
    def _200(self,content:str="All good!"):
        if type(content) == str:
            content:bytes = content.encode()
        self.send_response(200)
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):

        if self.path in ("/favicon.ico", "/"):
            r="big yikes"
        else:
            r=requests.get(self.path[1:]).content
        self._200(r)

def main():
    server = http.server.HTTPServer(('127.0.0.1',PORT),Server)
    print(f'Server started on :{PORT}')
    server.serve_forever()

if __name__ == '__main__': main()
