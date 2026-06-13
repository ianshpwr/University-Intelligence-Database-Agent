from scrapers.browser import BrowserManager
from scrapers.parser import HTMLParser


class UniversityExtractor:

    def __init__(self):
        self.browser = BrowserManager()

    def extract_basic_info(self, university):

        html = self.browser.fetch_html(
            university["url"]
        )

        soup = HTMLParser.parse(html)

        title = ""

        if soup.title:
            title = soup.title.text.strip()

        return {
            "name": university["name"],
            "title": title,
            "source_url": university["url"]
        }