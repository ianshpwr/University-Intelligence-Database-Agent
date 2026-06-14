from scrapers.browser import BrowserManager

from bs4 import BeautifulSoup

from scrapers.extractor import (
    UniversityExtractor
)

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/residence"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

extractor = UniversityExtractor()

costs = extractor.extract_living_costs(
    soup
)

print(
    "COSTS:",
    len(costs)
)

for item in costs[:20]:

    print(item)