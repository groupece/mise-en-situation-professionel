# DocuHelp Backend

API FastAPI pour authentification, upload/ingestion, recherche et réponses avec citations.

## Windows / PowerShell
```powershell
cd backend
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .\.env.example .\.env -Force
python -m uvicorn app.main:app --reload
```

## macOS / Linux
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs
Health: http://localhost:8000/health

Smoke test: register → login → Authorize → upload → ingest → search → answers. 