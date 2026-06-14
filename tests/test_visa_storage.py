from scrapers.browser import BrowserManager

from bs4 import BeautifulSoup

from scrapers.extractor import (
    UniversityExtractor
)

from database.repository import (
    save_visa_policy
)

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/international-students/study-permits"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

extractor = UniversityExtractor()

policies = extractor.extract_visa_policies(
    soup
)

for policy in policies:

    policy["university"] = (
        "University of Waterloo"
    )

    save_visa_policy(
        policy
    )

print(
    "Saved",
    len(policies),
    "visa policies"
)