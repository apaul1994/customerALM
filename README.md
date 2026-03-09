# Customer Analyzer API

A FastAPI-based application for analyzing customer entities.

## Features

- Analyze entities for matching scores with reference content
- Check for involvement in criminal activities
- Check for involvement in monetary fraud
- Fetch article content and publication date from URLs (optional)

## API Endpoints

### POST /api/v1/customer/analyze

Analyzes an entity based on name, description, and country. Optionally fetches article content and date if URL is provided.

**Request Body:**
```json
{
  "entity_name": "string",
  "entity_description": "string",
  "country": "string",
  "url": "string"  // optional
}
```

**Response:**
```json
{
  "matching_score": 0,
  "involved_in_criminal_activity": false,
  "involved_in_monetary_fraud": false,
  "content": "string",
  "date": "string"
}
```

## Installation

1. Clone the repository
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

## Running the Application

Run the application with: `python -m app.main`

Or use uvicorn: `uvicorn app.main:app --reload`

The API will be available at http://localhost:8000

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

## Project Structure

```
app/
├── api/
│   └── v1/
│       ├── endpoints/
│       │   └── customer.py
│       └── router.py
├── core/
│   └── logger.py
├── models/
│   └── schemas.py
├── services/
│   └── customer_service.py
└── main.py
```

## Architecture

- **Controllers (Endpoints):** Handle HTTP requests and responses
- **Services:** Contain business logic
- **Models:** Define data schemas
- **Core:** Configuration and utilities like logging