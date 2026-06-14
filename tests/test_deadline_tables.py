from scrapers.browser import BrowserManager
from bs4 import BeautifulSoup

browser = BrowserManager()

html = browser.fetch_html(
    "https://uwaterloo.ca/future-students/admissions/application-deadlines"
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

    rows = table.find_all("tr")

    print(
        "\nTABLE",
        i + 1,
        "ROWS:",
        len(rows)
    )

    for row in rows[:3]:

        print(
            row.get_text(
                " | ",
                strip=True
            )
        )