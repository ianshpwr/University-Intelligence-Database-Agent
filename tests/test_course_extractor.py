from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup
from scrapers.extractor import UniversityExtractor

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

print(
    "COURSES FOUND:",
    len(courses)
)

for course in courses[:20]:
    print(course)