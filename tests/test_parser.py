from scrapers.browser import BrowserManager
from scrapers.parser import HTMLParser

browser = BrowserManager()

html = browser.fetch_html(
    "https://www.unimelb.edu.au"
)

print(html[:1000])