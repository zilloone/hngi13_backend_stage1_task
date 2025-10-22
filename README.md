# String Analyzer Service (FastAPI)

## What
A REST API to analyze strings, store their computed properties and query them. Implements:
- POST /strings
- GET /strings/{string_value}
- GET /strings (with filters)
- GET /strings/filter-by-natural-language?query=...
- DELETE /strings/{string_value}

## Quick start (locally)
1. Clone repo
2. Create virtualenv and install deps:
   python -m venv .venv
   source .venv/bin/activate # On windows venv\Scripts\activate
   pip install -r requirements.txt

3. Run the server:
   fastapi dev

4. API docs:
   - Open http://localhost:8000/docs (Swagger UI)
   
