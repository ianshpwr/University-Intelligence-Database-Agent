from scrapers.extractor import UniversityExtractor
from database.repository import save_tuition
from exporters.json_exporter import JSONExporter
from exporters.csv_exporter import CSVExporter

with open(
    "data/raw/university_of_waterloo_tuition.txt",
    "r",
    encoding="utf-8"
) as f:

    text = f.read()

extractor = UniversityExtractor()

fees = extractor.extract_tuition(text)

print("FEES FOUND:", len(fees))

for fee in fees:

    fee["university"] = (
        "University of Waterloo"
    )

    fee["currency"] = "CAD"

    fee["source_url"] = (
        "https://uwaterloo.ca/future-students/financing/tuition"
    )

    save_tuition(fee)

    print(fee)

exporter = JSONExporter()

exporter.export_tuition()

csv_exporter = CSVExporter()

csv_exporter.export_universities()
csv_exporter.export_tuition()

print("Pipeline completed")
