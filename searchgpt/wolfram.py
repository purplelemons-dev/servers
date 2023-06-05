"""
# Wolfram API.
"""
import requests
from .env import WOLFRAM_APP_ID

def query(search:str) -> list[dict[str,]]:
    """Query Wolfram for a search.

    Args:
        search (str): The search query.

    Returns:
        list[dict[str,]]: A list of Wolfram Alpha answer pods.
    """
    return requests.get(
        "https://api.wolframalpha.com/v2/query",
        params={
            "format" : "plaintext",
            "input"  : search,
            "output" : "json",
            "appid"  : WOLFRAM_APP_ID
        }
    ).json()["queryresult"]["pods"]

if __name__ == "__main__":
    print(query("circumference of the sun"))
