def validate_university(data: dict):

    errors = []

    if not data.get("name"):
        errors.append("Missing university name")

    if data.get("founded_year"):

        year = data["founded_year"]

        if year < 1000 or year > 2026:
            errors.append("Invalid founded year")

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
