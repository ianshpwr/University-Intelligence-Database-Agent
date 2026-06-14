# scrapers/extractor.py
import re

from bs4 import BeautifulSoup

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

    def extract_scholarships(self, soup):

        import re

        scholarships = []

        headings = soup.find_all(
            ["h2", "h3", "h4"]
        )

        for heading in headings:

            title = heading.get_text(
                strip=True
            )

            if "Scholarship" not in title:
                continue

            next_block = heading.find_next(
                ["div", "article", "section"]
            )

            if not next_block:
                continue

            text = next_block.get_text(
                " ",
                strip=True
            )

            amount_match = re.search(
                r"\$([0-9,]+)",
                text
            )

            if not amount_match:
                continue

            scholarships.append({
                "name": title,
                "amount": float(
                    amount_match.group(1)
                    .replace(",", "")
                )
            })

        return scholarships
                
    def extract_living_costs(
        self,
        soup
    ):

        results = []

        tables = soup.find_all("table")

        for table in tables:

            rows = table.find_all("tr")

            for row in rows[1:]:

                cols = row.find_all(
                    ["td", "th"]
                )

                if len(cols) < 2:
                    continue

                category = cols[0].get_text(
                    " ",
                    strip=True
                )

                amount = cols[1].get_text(
                    " ",
                    strip=True
                )

                if "$" not in amount:
                    continue

                results.append({

                    "category": category,

                    "amount": amount,

                    "currency": "CAD"

                })

        return results


    def extract_deadlines(
        self,
        soup
    ):

        results = []

        tables = soup.find_all(
            "table"
        )

        for table in tables:

            rows = table.find_all(
                "tr"
            )

            if len(rows) < 2:
                continue

            headers = [

                th.get_text(
                    " ",
                    strip=True
                ).lower()

                for th in rows[0].find_all(
                    ["th", "td"]
                )
            ]

            deadline_column = None

            for i, header in enumerate(
                headers
            ):

                if (
                    "deadline" in header
                    or "apply" in header
                    or "date" in header
                ):
                    deadline_column = i
                    break

            if deadline_column is None:
                continue

            for row in rows[1:]:

                cols = row.find_all(
                    ["td", "th"]
                )

                if len(cols) <= deadline_column:
                    continue

                intake = cols[0].get_text(
                    " ",
                    strip=True
                )

                deadline = cols[
                    deadline_column
                ].get_text(
                    " ",
                    strip=True
                )

                results.append({

                    "intake": intake,

                    "deadline": deadline

                })

        return results

    def extract_courses(
        self,
        soup
    ):

        courses = []

        seen = set()

        for link in soup.find_all("a"):

            href = link.get(
                "href",
                ""
            )

            title = link.get_text(
                strip=True
            )

            if not href:
                continue

            if not title:
                continue

            if "/programs/" not in href:
                continue

            if title in seen:
                continue

            seen.add(title)

            courses.append({
                "code": "",
                "title": title,
                "credits": "",
                "description": "",
                "prerequisites": "",
                "mode": ""
            })

        return courses

    def extract_visa_policies(
        self,
        soup
    ):

        text = soup.get_text(
            " ",
            strip=True
        )

        return [{

            "visa_type": "Study Permit",

            "processing_time": "",

            "requirements": text[:5000]

        }]