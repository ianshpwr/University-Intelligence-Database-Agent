from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/programs"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

for link in soup.find_all("a"):

    text = link.get_text(strip=True)

    if text == "Computer Science":

        print("LINK")
        print(link)

        print("\nATTRS")
        print(link.attrs)

        break