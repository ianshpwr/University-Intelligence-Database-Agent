from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/residence"
)

soup = BeautifulSoup(
    html,
    "html.parser"
)

tables = soup.find_all("table")

print(
    "TABLES:",
    len(tables)
)

for i, table in enumerate(tables):

    print("\n" + "=" * 50)
    print("TABLE", i + 1)

    rows = table.find_all("tr")

    for row in rows[:5]:

        print(
            row.get_text(
                " | ",
                strip=True
            )
        )