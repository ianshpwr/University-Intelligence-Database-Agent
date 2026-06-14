
from database.repository import (
    UniversityRepository,
    save_tuition,
    save_scholarship,
    save_living_cost,
    save_deadline,
    save_course,
    save_visa_policy
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

import sys


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

    print("Loading living costs...")

    html = browser.fetch_html(
        "https://uwaterloo.ca/future-students/living-on-campus"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    living_costs = extractor.extract_living_costs(
        soup
    )

    for item in living_costs:

        item["university"] = (
            "University of Waterloo"
        )

        item["currency"] = "CAD"

        save_living_cost(item)

    print(
        f"Saved {len(living_costs)} living costs"
    )


    print("Loading deadlines...")

    html = browser.fetch_html(
        "https://uwaterloo.ca/future-students/admissions/application-deadlines"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    deadlines = extractor.extract_deadlines(
        soup
    )

    for item in deadlines:

        item["university"] = (
            "University of Waterloo"
        )

        save_deadline(item)

    print(
        f"Saved {len(deadlines)} deadlines"
    )


    print("Loading courses...")

    html = browser.fetch_html(
        "https://uwaterloo.ca/future-students/programs"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    courses = extractor.extract_courses(
        soup
    )

    for item in courses:

        item["university"] = (
            "University of Waterloo"
        )

        save_course(item)

    print(
        f"Saved {len(courses)} courses"
    )


    print("Loading visa policies...")

    html = browser.fetch_html(
        "https://uwaterloo.ca/future-students/international-students/study-permits"
    )

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    visa_policies = extractor.extract_visa_policies(
        soup
    )

    for item in visa_policies:

        item["university"] = (
            "University of Waterloo"
        )

        save_visa_policy(item)

    print(
        f"Saved {len(visa_policies)} visa policies"
    )








def export_data():

    json_exporter = JSONExporter()

    json_exporter.export_universities()

    csv_exporter = CSVExporter()

    csv_exporter.export_universities()

    csv_exporter.export_university_data()

    print("Exports completed")


def scrape():

    load_waterloo()

    print("Scraping completed")


def export():

    export_data()

    print("Export completed")


def run_all():

    load_waterloo()

    export_data()

    print("Pipeline completed")


if __name__ == "__main__":

    command = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "all"
    )

    if command == "scrape":

        scrape()

    elif command == "export":

        export()

    elif command == "all":

        run_all()

    else:

        print("Usage:")
        print("  python run.py scrape")
        print("  python run.py export")
        print("  python run.py all")
