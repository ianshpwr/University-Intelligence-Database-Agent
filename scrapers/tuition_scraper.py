from scrapers.browser import BrowserManager
from scrapers.parser import HTMLParser


class TuitionScraper:

    def __init__(self):
        self.browser = BrowserManager()

    def scrape_page(self, university_name, url):

        html = self.browser.fetch_html(url)

        soup = HTMLParser.parse(html)

        text = soup.get_text(
            separator=" ",
            strip=True
        )

        return {
            "university": university_name,
            "source_url": url,
            "raw_text": text[:10000]
        }