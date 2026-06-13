from configs.loader import load_universities
from scrapers.extractor import UniversityExtractor
from database.repository import UniversityRepository

extractor = UniversityExtractor()
repo = UniversityRepository()

universities = load_universities()

for uni in universities:

    data = extractor.extract_basic_info(
        uni
    )

    record_id = repo.save(data)

    print(
        f"Saved {data['name']} -> ID {record_id}"
    )