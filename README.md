# Agent 34 - Result Analysis Agent

Agent 34 is a full-stack academic result analysis platform for institutions. It ingests semester result files, validates and reconciles records, computes deterministic metrics, and produces role-aware dashboards and reports. Gemini is used only for optional narrative generation; numerical metrics remain deterministic and verifiable.

## Architecture

The project contains a React and TypeScript frontend and a FastAPI backend. The backend uses a service layer over SQLAlchemy and PostgreSQL, with SQLite supported for local development. Alembic manages database migrations. Uploaded datasets are isolated by import batch so analytics always operate on the active validated dataset.

## Technology

- Frontend: React, TypeScript, Vite, Tailwind CSS, Recharts
- Backend: FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic
- Database: PostgreSQL for production; SQLite for simple local development
- Analytics: Pandas, NumPy, and SciPy
- Reports: ReportLab PDF generation
- Tests: pytest backend coverage and frontend build/lint checks

## Capabilities

- JWT authentication with secure password handling and refresh tokens
- Role-based access control (RBAC) and backend data-scope enforcement
- Optional multi-factor authentication (MFA)
- CSV and Excel result ingestion with schema, marks, grade, and total validation
- Deterministic pass/fail, grade, performance, and data-quality analytics
- Merit analysis and ranking views
- Internal versus external marks analysis
- Historical trends across imported result batches
- Intervention prioritization for at-risk cohorts, courses, and sections
- Optional Gemini narrative generation from verified metrics
- PDF reports and audit logging

## Repository Layout

```text
backend/
  backend/
    app/          FastAPI application, models, services, and APIs
    alembic/      Database migrations
    tests/        Backend test suite
    requirements.txt
frontend/
  result-analysis-agent/
    src/          React application source
    package.json
```

## Local Setup

### Backend

```powershell
cd backend/backend
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and set local values, especially JWT_SECRET_KEY.
uvicorn app.main:app --reload
```

The backend uses SQLite when configured for local development. For PostgreSQL, set `DATABASE_URL` to a PostgreSQL SQLAlchemy URL, run `alembic upgrade head`, and then run `python seed.py` if demo accounts are needed.

### Frontend

```powershell
cd frontend/result-analysis-agent
npm install
npm run dev
```

The development frontend is normally available at `http://localhost:5173` and the API at `http://localhost:8000`.

## Environment Variables

Use `backend/backend/.env.example` as the backend template and create a local `.env` that is never committed. Important settings include `DATABASE_URL`, `FRONTEND_URL`, `JWT_SECRET_KEY`, token expiry values, mark limits, grade mapping, upload/report directories, and the optional `LLM_API_KEY` and `LLM_MODEL` settings. The frontend may use `VITE_DEMO_MODE` for local demo behavior.

Never place API keys, database passwords, JWT secrets, MFA/TOTP secrets, or other credentials in source code, documentation, or `.env.example`.

## Testing

Run backend tests from `backend/backend`:

```powershell
pytest
```

Run frontend checks from `frontend/result-analysis-agent`:

```powershell
npm run lint
npm run build
```

## Deployment

For deployment, provide PostgreSQL connection settings and strong generated secrets through the platform's secret store or environment configuration. Apply Alembic migrations before starting the API, configure the frontend origin in `FRONTEND_URL`, persist upload/report storage as appropriate, and run the frontend production build. The backend Dockerfile and Docker Compose configuration provide a starting point for containerized deployments.
