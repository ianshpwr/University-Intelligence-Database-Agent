from scrapers.extractor import UniversityExtractor

with open(
    "data/raw/university_of_waterloo_tuition.txt",
    "r",
    encoding="utf-8"
) as f:

    text = f.read()

print("TEXT LENGTH:", len(text))

extractor = UniversityExtractor()

fees = extractor.extract_tuition(text)

print("FEES FOUND:", len(fees))

for fee in fees[:20]:
    print(fee)