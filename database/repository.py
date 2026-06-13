from database.db import SessionLocal
from database.models import University


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