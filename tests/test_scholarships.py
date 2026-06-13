from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/financing/scholarships"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

text = soup.get_text(
    separator=" ",
    strip=True
)

print(text[:5000])