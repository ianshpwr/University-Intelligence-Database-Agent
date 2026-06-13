from database.repository import save_tuition
from scrapers.tuition_scraper import (
    extract_waterloo_tuition
)

with open(
    "data/raw/university_of_waterloo_tuition.txt",
    "r",
    encoding="utf-8"
) as f:

    text = f.read()

fees = extract_waterloo_tuition(text)

for fee in fees:

    fee["university"] = "University of Waterloo"
    fee["currency"] = "CAD"

    fee["source_url"] = (
        "https://uwaterloo.ca/future-students/financing/tuition"
    )

    save_tuition(fee)

    print(fee)