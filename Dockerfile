FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# Install only pure-Python dependencies (no Playwright browsers needed)
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure data and output directories exist
RUN mkdir -p data output

EXPOSE 8000

# Initialize DB schema (idempotent), then start API
CMD ["sh", "-c", "python -m database.init_db && uvicorn api.main:app --host 0.0.0.0 --port 8000"]