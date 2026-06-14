import csv
import os

from database.repository import (
    get_all_universities,
    get_all_tuition,
    get_all_scholarships,
    get_all_courses,
    get_all_deadlines,
    get_all_living_costs,
    get_all_visa_policies
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
    def export_university_data(self):

        rows = []

        for fee in get_all_tuition():

            rows.append([
                fee.university,
                "tuition",
                fee.program,
                fee.international_fee,
                fee.source_url
            ])

        for item in get_all_scholarships():

            rows.append([
                item.university,
                "scholarship",
                item.name,
                item.amount,
                item.source_url
            ])

        for item in get_all_courses():

            rows.append([
                item.university,
                "course",
                item.title,
                item.code,
                ""
            ])

        for item in get_all_deadlines():

            rows.append([
                item.university,
                "deadline",
                item.intake,
                item.deadline,
                ""
            ])

        for item in get_all_living_costs():

            rows.append([
                item.university,
                "living_cost",
                item.category,
                item.amount,
                ""
            ])

        for item in get_all_visa_policies():

            rows.append([
                item.university,
                "visa_policy",
                item.visa_type,
                item.requirements,
                ""
            ])

        os.makedirs(
            "output",
            exist_ok=True
        )

        with open(
            "output/university_data.csv",
            "w",
            newline="",
            encoding="utf-8"
        ) as f:

            writer = csv.writer(f)

            writer.writerow([
                "university",
                "data_type",
                "title",
                "value",
                "source_url"
            ])

            writer.writerows(rows)
