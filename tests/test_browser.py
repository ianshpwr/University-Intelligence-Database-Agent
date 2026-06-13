from scrapers.browser import BrowserManager

browser = BrowserManager()

html = browser.fetch_html(
    "https://www.unimelb.edu.au"
)

print(len(html))