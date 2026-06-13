from pydantic import BaseModel


class UniversitySchema(BaseModel):
    name: str
    country: str | None = None
    city: str | None = None
    type: str | None = None
    founded_year: int | None = None
    ranking: str | None = None
    source_url: str | None = None