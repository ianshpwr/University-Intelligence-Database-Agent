from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

urls = [
    "https://www.ualberta.ca",
    "https://uwaterloo.ca",
    "https://www.asu.edu"
]

browser = BrowserManager()

for url in urls:
    try:
        html = browser.fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        title = soup.title.text.strip() if soup.title else "NO TITLE"

        print("\n================")
        print(url)
        print(title)

    except Exception as e:
        print(url, e)