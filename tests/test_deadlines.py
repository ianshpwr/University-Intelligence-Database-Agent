from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/admissions/application-deadlines"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

tables = soup.find_all("table")

print(
    "TABLES FOUND:",
    len(tables)
)

if tables:

    print(
        tables[0].prettify()[:5000]
    )