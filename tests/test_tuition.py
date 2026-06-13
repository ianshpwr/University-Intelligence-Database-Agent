from configs.loader import load_universities
from scrapers.tuition_scraper import TuitionScraper

scraper = TuitionScraper()

universities = load_universities()

for uni in universities:

    result = scraper.scrape_page(
        uni["name"],
        uni["tuition_url"]
    )

    print("\n")
    print("=" * 50)
    print(result["university"])
    print("=" * 50)

    print(
        result["raw_text"][:500]
    )