from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup
from scrapers.extractor import UniversityExtractor

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/financing/scholarships"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

extractor = UniversityExtractor()

results = extractor.extract_scholarships(
    soup
)

for item in results:
    print(item)