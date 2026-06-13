from database.db import SessionLocal
from database.models import University
from database.models import TuitionFee
from database.models import Scholarship

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

def get_all_universities():

    session = SessionLocal()

    try:

        return session.query(
            University
        ).all()

    finally:

        session.close()


def get_all_tuition():

    session = SessionLocal()

    try:

        return session.query(
            TuitionFee
        ).all()

    finally:

        session.close


def get_university_by_id(university_id):

    session = SessionLocal()

    try:

        return session.query(
            University
        ).filter(
            University.id == university_id
        ).first()

    finally:

        session.close()


def get_tuition_by_university(university_name):

    session = SessionLocal()

    try:

        return session.query(
            TuitionFee
        ).filter(
            TuitionFee.university == university_name
        ).all()

    finally:

        session.close()

def save_scholarship(data):

    session = SessionLocal()

    try:

        scholarship = Scholarship(
            university=data["university"],
            name=data["name"],
            amount=data["amount"],
            source_url=data["source_url"]
        )

        session.add(scholarship)

        session.commit()

    finally:

        session.close()