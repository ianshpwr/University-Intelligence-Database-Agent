from scrapers.browser import BrowserManager

from bs4 import BeautifulSoup

from scrapers.extractor import (
    UniversityExtractor
)

from database.repository import (
    save_living_cost
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

for cost in costs:

    cost["university"] = (
        "University of Waterloo"
    )

    save_living_cost(
        cost
    )

print(
    "Saved",
    len(costs),
    "living costs"
)