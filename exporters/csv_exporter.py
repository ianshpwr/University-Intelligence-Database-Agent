import csv
import os

from database.repository import (
    get_all_universities,
    get_all_tuition
)


class CSVExporter:

    def export_universities(self):

        universities = get_all_universities()

        os.makedirs(
            "output",
            exist_ok=True
        )

        with open(
            "output/universities.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "id",
                "name",
                "source_url"
            ])

            for university in universities:

                writer.writerow([
                    university.id,
                    university.name,
                    university.source_url
                ])

    def export_tuition(self):

        tuition_fees = get_all_tuition()

        os.makedirs(
            "output",
            exist_ok=True
        )

        with open(
            "output/tuition_fees.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "id",
                "university",
                "program",
                "domestic_fee",
                "international_fee",
                "currency",
                "source_url"
            ])

            for fee in tuition_fees:

                writer.writerow([
                    fee.id,
                    fee.university,
                    fee.program,
                    fee.domestic_fee,
                    fee.international_fee,
                    fee.currency,
                    fee.source_url
                ])
