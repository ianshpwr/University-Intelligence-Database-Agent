from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text

Base = declarative_base()


class University(Base):
    __tablename__ = "universities"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    country = Column(String)
    city = Column(String)
    type = Column(String)
    founded_year = Column(Integer)
    ranking = Column(String)
    source_url = Column(Text)
