from configs.loader import load_universities
from scrapers.extractor import UniversityExtractor

extractor = UniversityExtractor()

universities = load_universities()

for uni in universities:

    result = extractor.extract_basic_info(
        uni["url"]
    )

    print(result)