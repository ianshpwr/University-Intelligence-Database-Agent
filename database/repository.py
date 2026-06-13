from database.db import SessionLocal
from database.models import University
from database.models import TuitionFee

class UniversityRepository:

    def save(self, data: dict):

        session = SessionLocal()

        try:

            university = University(
                name=data.get("name"),
                source_url=data.get("source_url")
            )

            session.add(university)

            session.commit()

            session.refresh(university)

            return university.id

        finally:

            session.close()



def save_tuition(data):

    session = SessionLocal()

    try:

        fee = TuitionFee(
            university=data["university"],
            program=data["program"],
            domestic_fee=data["domestic_fee"],
            international_fee=data["international_fee"],
            currency=data["currency"],
            source_url=data["source_url"]
        )

        session.add(fee)

        session.commit()

    finally:

        session.close()