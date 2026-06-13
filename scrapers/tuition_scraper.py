import re


def extract_waterloo_tuition(text):

    results = []

    programs = {
        "Computer Science": {
            "domestic": r"Computer Science \$([0-9,]+)",
            "international": r"Computer Science \$([0-9,]+).*?\$1,500"
        },
        "Engineering": {
            "domestic": r"Faculty of Engineering, Software Engineering \$([0-9,]+)",
            "international": r"Faculty of Engineering, Software Engineering \$([0-9,]+).*?\$1,500"
        },
        "Arts": {
            "domestic": r"Faculty of Arts \$([0-9,]+)",
            "international": r"Faculty of Arts \$([0-9,]+).*?\$1,500"
        }
    }

    international_section = text.split(
        "International (visa) students"
    )[-1]

    for program, patterns in programs.items():

        domestic_match = re.search(
            patterns["domestic"],
            text
        )

        international_match = re.search(
            patterns["international"],
            international_section
        )

        if domestic_match and international_match:

            results.append(
                {
                    "program": program,
                    "domestic_fee": float(
                        domestic_match.group(1).replace(",", "")
                    ),
                    "international_fee": float(
                        international_match.group(1).replace(",", "")
                    )
                }
            )

    return results