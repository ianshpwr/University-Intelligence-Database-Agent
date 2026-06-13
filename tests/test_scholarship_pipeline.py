from scrapers.browser import BrowserManager
from scrapers.extractor import UniversityExtractor

from bs4 import BeautifulSoup

from database.repository import (
    save_scholarship
)

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/financing/scholarships"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

extractor = UniversityExtractor()

scholarships = (
    extractor.extract_scholarships(
        soup
    )
)

for scholarship in scholarships:

    scholarship["university"] = (
        "University of Waterloo"
    )

    scholarship["source_url"] = (
        "https://uwaterloo.ca/future-students/financing/scholarships"
    )

    save_scholarship(
        scholarship
    )

    print(
        scholarship
    )

print(
    "Scholarships saved"
)