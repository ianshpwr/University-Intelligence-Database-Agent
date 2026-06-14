from scrapers.browser import BrowserManager

from bs4 import BeautifulSoup

from scrapers.extractor import (
    UniversityExtractor
)

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/admissions/application-deadlines"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

extractor = UniversityExtractor()

deadlines = (
    extractor.extract_deadlines(
        soup
    )
)

print(
    "DEADLINES:",
    len(deadlines)
)

for item in deadlines[:20]:

    print(item)