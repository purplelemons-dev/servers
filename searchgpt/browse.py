
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def browse(url:str) -> str:
    """Essentially returns `document.body.innerText` of a webpage."""
    driver.get(url)
    return driver.find_element("xpath", "/html/body").text

if __name__ == "__main__":
    url = "https://solarsystem.nasa.gov/solar-system/sun/by-the-numbers/"
    print(browse(url))
