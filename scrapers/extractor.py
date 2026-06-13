# scrapers/extractor.py

import re

class UniversityExtractor:

    def extract_tuition(self, text):

        domestic_section, international_section = \
            self.split_tuition_sections(text)

        domestic = self.extract_program_fee_pairs(
            domestic_section
        )

        international = self.extract_program_fee_pairs(
            international_section
        )

        return self.merge_fee_sections(
            domestic,
            international
        )

    def split_tuition_sections(self, text):

        marker = "International (visa) students"

        if marker not in text:
            return text, ""

        parts = text.split(marker)

        return parts[0], parts[1]

    def extract_program_fee_pairs(self, section):

        pattern = r"([A-Za-z0-9,&/\-\(\)\s]+?)\s+\$([0-9,]+)"

        matches = re.findall(pattern, section)

        results = {}

        for program, fee in matches:

            program = self.clean_program_name(
                program
            )

            if not self.is_valid_program(
                program
            ):
                continue

            results[program] = float(
                fee.replace(",", "")
            )

        return results

    def merge_fee_sections(
        self,
        domestic,
        international
    ):

        programs = (
            set(domestic.keys())
            &
            set(international.keys())
        )

        results = []

        for program in programs:

            results.append({
                "program": program,
                "domestic_fee":
                    domestic[program],
                "international_fee":
                    international[program]
            })

        return results

    def clean_program_name(self, name):

        name = re.sub(
            r"^\d+,\d+\s+",
            "",
            name
        )

        return name.strip()

    def is_valid_program(self, name):

        invalid = [
            "Co-op students",
            "Fees are estimates",
            "Books, supplies",
            "You pay fees"
        ]

        return (
            len(name) > 5
            and
            not any(
                x in name
                for x in invalid
            )
        )