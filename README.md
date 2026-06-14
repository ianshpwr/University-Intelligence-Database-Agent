# University Intelligence

A data collection and intelligence platform that extracts university information, stores it in SQLite, exposes it through FastAPI, and exports structured datasets.

## Features

* Web scraping pipeline
* SQLite database storage
* FastAPI REST API
* CSV export
* JSON export

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
