from database.repository import (
    UniversityRepository,
    save_tuition,
    save_scholarship
)

from exporters.json_exporter import (
    JSONExporter
)

from exporters.csv_exporter import (
    CSVExporter
)

from scrapers.extractor import (
    UniversityExtractor
)

from scrapers.browser import (
    BrowserManager
)

from bs4 import BeautifulSoup


def load_waterloo():

    repo = UniversityRepository()

    repo.save({
        "name": "University of Waterloo",
        "source_url": "https://uwaterloo.ca"
    })

    browser = BrowserManager()

    extractor = UniversityExtractor()

    print("Loading tuition...")

    with open(
        "data/raw/university_of_waterloo_tuition.txt",
        "r",
        encoding="utf-8"
    ) as f:

        text = f.read()

    fees = extractor.extract_tuition(
        text
    )

    for fee in fees:

        fee["university"] = (
            "University of Waterloo"
        )

        fee["currency"] = "CAD"

        fee["source_url"] = (
            "https://uwaterloo.ca/future-students/financing/tuition"
        )

        save_tuition(fee)

    print(
        f"Saved {len(fees)} tuition records"
    )

    print("Loading scholarships...")

    html = browser.fetch_html(
        "https://uwaterloo.ca/future-students/financing/scholarships"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    scholarships = (
        extractor.extract_scholarships(
            soup
        )
    )

    for scholarship in scholarships:

        scholarship["university"] = (
            "University of Waterloo"
        )

        scholarship["source_url"] = (
            "https://uwaterloo.ca/future-students/financing/scholarships"
        )

        save_scholarship(
            scholarship
        )

    print(
        f"Saved {len(scholarships)} scholarships"
    )


def export_data():

    json_exporter = JSONExporter()

    json_exporter.export_universities()

    csv_exporter = CSVExporter()

    csv_exporter.export_universities()

    csv_exporter.export_university_data()

    print("Exports completed")


if __name__ == "__main__":

    load_waterloo()

    export_data()

    print("Pipeline completed")
