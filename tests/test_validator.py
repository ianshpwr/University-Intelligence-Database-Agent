from validators.validator import validate_university

sample = {
    "name": "University of Melbourne",
    "founded_year": 1853
}

print(validate_university(sample))