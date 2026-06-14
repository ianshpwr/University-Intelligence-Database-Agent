from scrapers.browser import BrowserManager

from bs4 import BeautifulSoup

from scrapers.extractor import (
    UniversityExtractor
)

from database.repository import (
    save_deadline
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

for deadline in deadlines:

    deadline["university"] = (
        "University of Waterloo"
    )

    save_deadline(
        deadline
    )

print(
    "Saved",
    len(deadlines),
    "deadlines"
)