# University Intelligence

⚠️ **Project Status**

This project was built in approximately **1 day** as part of an assignment.

The current implementation is a working MVP focused on demonstrating:

* Data extraction
* Data storage
* API development
* Data export
* Docker deployment

The scraping logic is currently optimized for the University of Waterloo and serves as a foundation for future expansion.

Future improvements include:

* Generalizing extractors across multiple universities
* Reducing website-specific parsing logic
* Improving data validation
* Expanding university coverage
* Improving extraction accuracy and maintainability

## Features

* Web scraping pipeline
* SQLite database storage
* FastAPI REST API
* CSV export
* JSON export
* Docker support

## Data Collected

* Tuition Fees
* Scholarships
* Courses
* Application Deadlines
* Living Costs
* Visa Policies

## Setup

```bash
pip install -r requirements.txt
```

## Commands

```bash
python run.py scrape
python run.py export
python run.py all
```

## Run API

```bash
uvicorn api.main:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## Docker

Build:

```bash
docker compose build
```

Run:

```bash
docker compose up
```

Stop:

```bash
docker compose down
```

Swagger UI:

```text
http://localhost:8000/docs
```

## API Endpoints

```http
GET /health
GET /universities
GET /universities/{id}
```

## Output

```text
output/
├── university_data.csv
└── university_data.json
```
