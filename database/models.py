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