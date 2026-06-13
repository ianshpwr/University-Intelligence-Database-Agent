import json
import os

from database.repository import (
    get_all_universities,
    get_all_tuition
)


class JSONExporter:

    def export_universities(self):

        universities = get_all_universities()

        data = []

        for university in universities:

            data.append({
                "id": university.id,
                "name": university.name,
                "source_url": university.source_url
            })

        os.makedirs(
            "output",
            exist_ok=True
        )

        with open(
            "output/universities.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )

    def export_tuition(self):

        tuition_fees = get_all_tuition()

        data = []

        for fee in tuition_fees:

            data.append({
                "id": fee.id,
                "university": fee.university,
                "program": fee.program,
                "domestic_fee": fee.domestic_fee,
                "international_fee": fee.international_fee,
                "currency": fee.currency,
                "source_url": fee.source_url
            })

        os.makedirs(
            "output",
            exist_ok=True
        )

        with open(
            "output/tuition_fees.json",
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                data,
                f,
                indent=4
            )