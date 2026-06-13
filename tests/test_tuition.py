from configs.loader import load_universities
from scrapers.tuition_scraper import TuitionScraper

scraper = TuitionScraper()

universities = load_universities()

for uni in universities:

    result = scraper.scrape_page(
        uni["name"],
        uni["tuition_url"]
    )

    filename = (
        uni["name"]
        .lower()
        .replace(" ", "_")
        + "_tuition.txt"
    )

    with open(
        f"data/raw/{filename}",
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            result["raw_text"]
        )

    print(
        f"Saved {filename}"
    )