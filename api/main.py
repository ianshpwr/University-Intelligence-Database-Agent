from fastapi import FastAPI, HTTPException

from database.repository import (
    get_all_universities,
    get_university_by_id,
    get_tuition_by_university,
    get_scholarships_by_university
)

app = FastAPI(
    title="University Intelligence API"
)


@app.get("/health")
def health():

    return {
        "status": "ok"
    }


@app.get("/universities")
def universities():

    data = get_all_universities()

    return [
        {
            "id": university.id,
            "name": university.name
        }
        for university in data
    ]


@app.get("/universities/{university_id}")
def university_details(
    university_id: int
):

    university = get_university_by_id(
        university_id
    )

    if not university:

        raise HTTPException(
            status_code=404,
            detail="University not found"
        )

    tuition = get_tuition_by_university(
        university.name
    )
    scholarships = (
    get_scholarships_by_university(
        university.name
    )
)

    return {
        "id": university.id,
        "name": university.name,
        "source_url": university.source_url,

        "tuition": [

            {
                "program": fee.program,
                "domestic_fee":
                    fee.domestic_fee,
                "international_fee":
                    fee.international_fee,
                "currency":
                    fee.currency
            }

            for fee in tuition
        ],

        "scholarships": [

    {
        "name": item.name,
        "amount": item.amount
    }

    for item in scholarships
                            ],
        "courses": [],
        "living_costs": [],
        "deadlines": [],
        "visa_policies": []
    }