from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/international-students/study-permits"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

print(
    soup.title.text
)

text = soup.get_text(
    " ",
    strip=True
)

print(
    text[:5000]
)