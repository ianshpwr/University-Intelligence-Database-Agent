from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text


Base = declarative_base()


class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True)

    name = Column(String)
    country = Column(String)
    city = Column(String)
    university_type = Column(String)

    founded_year = Column(Integer)
    ranking = Column(String)

    acceptance_rate = Column(Float)

    graduate_employment_rate = Column(Float)
    graduate_employment_year = Column(String)

    average_salary = Column(String)

    source_url = Column(Text)

class TuitionFee(Base):
    __tablename__ = "tuition_fees"

    id = Column(Integer, primary_key=True)

    university = Column(String)

    program = Column(String)

    domestic_fee = Column(Float)

    international_fee = Column(Float)

    currency = Column(String)

    source_url = Column(String)

class Scholarship(Base):

    __tablename__ = "scholarships"

    id = Column(
        Integer,
        primary_key=True
    )

    university = Column(String)

    name = Column(String)

    amount = Column(Float)

    source_url = Column(String)


class LivingCost(Base):
    __tablename__ = "living_costs"

    id = Column(Integer, primary_key=True)

    university = Column(String)

    category = Column(String)

    amount = Column(String)

    currency = Column(String)


class Deadline(Base):
    __tablename__ = "deadlines"

    id = Column(Integer, primary_key=True)

    university = Column(String)

    intake = Column(String)

    deadline = Column(String)


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)

    university = Column(String)

    code = Column(String)

    title = Column(String)

    credits = Column(String)

    description = Column(Text)

    prerequisites = Column(Text)

    mode = Column(String)


class VisaPolicy(Base):
    __tablename__ = "visa_policies"

    id = Column(Integer, primary_key=True)

    university = Column(String)

    visa_type = Column(String)

    processing_time = Column(String)

    requirements = Column(Text)