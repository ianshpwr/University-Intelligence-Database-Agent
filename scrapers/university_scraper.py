from scrapers.browser import BrowserManager
from scrapers.parser import HTMLParser


class UniversityScraper:

    def __init__(self):
        self.browser = BrowserManager()

    def scrape_homepage(self, url):

        html = self.browser.fetch_html(url)

        soup = HTMLParser.parse(html)

        return {
            "title": soup.title.text.strip()
        }