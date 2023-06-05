# executes module script pogggg
from .wolfram import query as wolfram_query
from .google import query as google_query
from .ai_api import extract_query as extractor, AI
from .browse import browse
from json import dumps, loads
from random import getrandbits as grb
from base64 import b64encode as b64e
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

sha = lambda x: sha256(x).hexdigest()
"`(x:bytes) -> str` Returns the sha256 hash of `x` as a hex string."

# big ai = gpt4
# small ai = gpt3.5

# big ai exists: $main
# user can ask ai questions: $query
# big ai has the choice to answer || (to outsource the question to google || wolfram)
# if google:
#  google answers with a list of text excerpts from 10 pages: $excerpts
#  small ai extractor( answers, $query ) in $excerpts
#  small ai extracts the best answer based on $query || chooses to browse best page
#  if browse:
#   new big ai summarizes document.body.innerText of page: $summary
#   $summary is sent to $main
#  if answer:
#   $answer is sent to $main
# if wolfram:
#  wolfram gives queryresults in pods: $pods
#  small ai extractor( $pods, $query ): $answer
#  $answer is sent to $main

from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    conversations:dict[str,AI] = {}

    def json(self, data:dict=None, code:int=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if data is not None: self.wfile.write(dumps(data).encode())

    def body(self) -> dict:
        return loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
    
    def on_request(self):
        parsed = urlparse(self.path)
        self.path = parsed.path
        self.query = parse_qs(parsed.query)

    def do_GET(self):
        self.on_request()

        if not self.path.startswith("/v1"):
            self.json({"error": "invalid path"}, 404)
            return

        elif self.path.startswith("/v1/search/new"):
            # create auth token and use the hash as a key, give the token to the client
            token = b64e(str(grb(144)).encode())
            self.conversations[sha(token)] = AI()
            self.json({"token": token.decode()})
            return
        
        elif self.path.startswith("/v1/search"):
            search_id = self.query.get("id", [None])[0]
            if search_id is None or sha(search_id.encode()) not in self.conversations:
                # redirect to /v1/search/new if no id is given
                self.send_response(302)
                self.send_header("Location", "/v1/search/new")
                self.end_headers()
                return
            
            self.json(self.conversations[sha(search_id.encode())].to_dict())
            return

    def do_POST(self):
        self.on_request()

        if not self.path.startswith("/v1"):
            self.json({"error": "invalid path"}, 404)
            return

        elif self.path.startswith("/v1/search"):
            # the user is sending a message to the ai in the body
            search_id = self.query.get("id", [None])[0]
            if search_id is None or sha(search_id.encode()) not in self.conversations:
                self.json({"error": "invalid id, get a new one at 'GET /search/new'"}, 400)
                return
            ai = self.conversations[sha(search_id.encode())]
            body = self.body()
            if "message" not in body:
                self.json({"error": "invalid body, expected 'message'"}, 400)
                return
            message:str = body["message"]
            ai.add("user", message)
            response = ai.generate()
            print("DEBUG", response)
            if "message" in response:
                response = response["message"]
                self.conversations[sha(search_id.encode())].add("assistant", response)
                self.json({"message": response})
                return
            elif "command" in response and "input" in response:
                if response["command"] == "google":
                    print("used google", response["input"])
                    google_results = google_query(response["input"])
                    response["results"] = "\n".join(f"#{idx}. {result}" for idx,result in enumerate(google_results))

                elif response["command"] == "wolfram":
                    print("used wolfram", response["input"])
                    response["results"] = wolfram_query(response["input"])
                else:
                    self.json({"error": "invalid command"}, 400)
                    return
                google = response["command"]=="google"
                ai_google_search = response["input"]
                print("DEBUG", response["results"])
                answer, wants_to_read = extractor(
                    response["results"],
                    ai_google_search,
                    google=google
                )
                print(f"1 {answer=} {wants_to_read=}")
                if google and wants_to_read:
                    # answer should have the page # at the front (since we only use 10 results and wer're 0-indexing, we can just grab the first digit)
                    print("used browse")
                    site = browse(google_results[int(answer[0])].url)
                    answer, _ = extractor(
                        site,
                        ai_google_search
                    )
                    print(f"2 {answer=} {wants_to_read=}")
                self.conversations[sha(search_id.encode())].add("assistant", answer)
                self.json({"message": answer})
                return
            else:
                self.json({"error": "invalid response from ai"}, 500)
                return


server = HTTPServer(("127.0.0.1", 10004), Handler)
server.serve_forever()
