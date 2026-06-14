# University Intelligence

⚠️ **Project Status**

This project was built in approximately **1 day** as part of an assignment

It is currently a working MVP focused on demonstrating:

* Web scraping
* Data storage
* API development
* Data export
* Docker deployment

The current implementation is primarily optimized for the University of Waterloo. Future iterations will focus on generalizing extraction logic across multiple universities and simplifying scraper maintenance.

---

## What does this project do?

This project collects university information from public university websites and stores it in a structured database.

The collected data can then be:

* Queried through a REST API
* Exported as CSV
* Exported as JSON

---

## Data Collected

* Tuition Fees
* Scholarships
* Courses
* Application Deadlines
* Living Costs
* Visa Policies

---

# Quick Start (Docker Recommended)

### 1. Clone the repository

```bash
git clone https://github.com/ianshpwr/University-Intelligence-Database-Agent.git
cd University-Intelligence-Database-Agent
```

# Local Setup (Without Docker)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Collect data

```bash
python run.py scrape
```

### Export data

```bash
python run.py export
```

### Run complete pipeline

```bash
python run.py all
```

### Start API

```bash
uvicorn api.main:app --reload
```

### 2. Build the Docker image

```bash
docker compose build
```

### 3. Start the API

```bash
docker compose up
```

### 4. Open Swagger Documentation

```text
http://localhost:8000/docs
```

### Stop Docker

```bash
docker compose down
```

---

## API Endpoints

```http
GET /health
GET /universities
GET /universities/{id}
```

---

## Output Files

After running:

```bash
python run.py export
```

generated files are available in:

```text
output/
├── university_data.csv
└── university_data.json
```

---

## Project Structure

```text
api/
database/
exporters/
scrapers/
tests/
output/
data/
run.py
```

---

## Future Improvements

* Multi-university support
* More generalized extraction logic
* Better validation and error handling
* Additional export formats
* Automated scraping schedules
* Improved API filtering and search

```
```
