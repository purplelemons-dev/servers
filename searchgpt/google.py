
import requests
from searchgpt.env import GOOGLE_API_KEY, GOOGLE_ENGINE

class Summary:
    def __init__(self, title:str, url:str, text:str) -> None:
        self.title = title
        self.url = url
        self.text = text

    def __repr__(self) -> str:
        return f"{self.title}: {self.text}"

    def __str__(self) -> str:
        return self.__repr__()


def query(search:str) -> list[Summary]:
    """Query Google for a search.

    Args:
        search (str): The search query.

    Returns:
        list[Summary]: A list of the top 10 Google results.
    """
    return [
        Summary(
            title = result["title"],
              url = result["link"],
             text = result["snippet"]
        )
        for result in requests.get(
            "https://customsearch.googleapis.com/customsearch/v1",
            params={
                  "q" : search,
                 "cx" : GOOGLE_ENGINE,
                "key" : GOOGLE_API_KEY,
                "num" : 10
            }
        )
        .json()["items"]
    ]


if __name__ == "__main__":
    for idx,result in enumerate(query("circumference of the sun")):
        print(f"#{idx+1}) {result}")
