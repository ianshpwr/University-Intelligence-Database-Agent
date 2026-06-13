from scrapers.university_scraper import UniversityScraper

scraper = UniversityScraper()

data = scraper.scrape_homepage(
    "https://www.unimelb.edu.au"
)

print(data)