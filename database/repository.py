from database.db import SessionLocal
from database.models import University
from database.models import TuitionFee
from database.models import (
    Scholarship,
    LivingCost,
    Deadline,
    Course,
    VisaPolicy
)



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

        session.add(
            scholarship
        )

        session.commit()

    finally:

        session.close()


def get_scholarships_by_university(
    university_name
):

    session = SessionLocal()

    try:

        return session.query(
            Scholarship
        ).filter(
            Scholarship.university
            == university_name
        ).all()

    finally:

        session.close()

def save_living_cost(data):

    session = SessionLocal()

    try:

        item = LivingCost(
            university=data["university"],
            category=data["category"],
            amount=data["amount"],
            currency=data["currency"]
        )

        session.add(item)

        session.commit()

    finally:

        session.close()


def save_deadline(data):

    session = SessionLocal()

    try:

        item = Deadline(
            university=data["university"],
            intake=data["intake"],
            deadline=data["deadline"]
        )

        session.add(item)

        session.commit()

    finally:

        session.close()


def save_course(data):

    session = SessionLocal()

    try:

        item = Course(
            university=data["university"],
            code=data["code"],
            title=data["title"],
            credits=data["credits"],
            description=data["description"],
            prerequisites=data["prerequisites"],
            mode=data["mode"]
        )

        session.add(item)

        session.commit()

    finally:

        session.close()


def save_visa_policy(data):

    session = SessionLocal()

    try:

        item = VisaPolicy(
            university=data["university"],
            visa_type=data["visa_type"],
            processing_time=data["processing_time"],
            requirements=data["requirements"]
        )

        session.add(item)

        session.commit()

    finally:

        session.close()


def get_courses_by_university(
    university_name
):

    session = SessionLocal()

    try:

        return session.query(
            Course
        ).filter(
            Course.university
            == university_name
        ).all()

    finally:

        session.close()

def get_deadlines_by_university(
    university_name
):

    session = SessionLocal()

    try:

        return session.query(
            Deadline
        ).filter(
            Deadline.university
            == university_name
        ).all()

    finally:

        session.close()


def get_living_costs_by_university(
    university_name
):

    session = SessionLocal()

    try:

        return session.query(
            LivingCost
        ).filter(
            LivingCost.university
            == university_name
        ).all()

    finally:

        session.close()


def get_visa_policies_by_university(
    university_name
):

    session = SessionLocal()

    try:

        return session.query(
            VisaPolicy
        ).filter(
            VisaPolicy.university
            == university_name
        ).all()

    finally:

        session.close()