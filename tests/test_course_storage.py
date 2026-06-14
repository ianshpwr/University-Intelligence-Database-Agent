from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

from scrapers.extractor import UniversityExtractor

from database.repository import save_course

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/programs"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

extractor = UniversityExtractor()

courses = extractor.extract_courses(
    soup
)

for course in courses:

    course["university"] = (
        "University of Waterloo"
    )

    save_course(
        course
    )

print(
    "Saved",
    len(courses),
    "courses"
)