import json


def load_universities():

    with open(
        "configs/universities.json",
        "r"
    ) as f:

        return json.load(f)