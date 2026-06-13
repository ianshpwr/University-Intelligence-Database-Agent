from scrapers.tuition_scraper import TuitionExtractor

with open(
    "data/raw/university_of_waterloo_tuition.txt",
    "r",
    encoding="utf-8"
) as f:

    text = f.read()

print("TEXT LENGTH:", len(text))

extractor = TuitionExtractor()

fees = extractor.extract(text)

print("FEES FOUND:", len(fees))

for fee in fees[:20]:
    print(fee)