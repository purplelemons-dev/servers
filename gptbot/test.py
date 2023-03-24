
api_key = "AIzaSyC40ZLoiS3fNIsSSmqc56B0NYbsDUe0Cvw"
search_engine_id = "22b6102675f074222"

import requests

def google_search(query:str,num=5) -> list[str]:
    params = {
        "key": api_key,
        "cx": search_engine_id,
        "q": query,
        "num": 10
    }
    r = requests.get(f"https://customsearch.googleapis.com/customsearch/v1", params=params)
    if r.status_code == 200:
        return [item["link"] for item in r.json()["items"]]
    return []

if __name__ == "__main__":
    print(google_search("python"))
