# Agent 34 — Result Analysis Agent

**Agentic AI Platform for Academic Institutions**

Agent 34 is a complete post-result academic analytics platform. It ingests published semester results, validates and reconciles them, runs deterministic analysis, and generates actionable insights — optionally enhanced by Gemini AI narrative.

---

## Architecture

`
React + TypeScript Frontend (localhost:5173)
              |  Axios / HTTPS
              v
FastAPI REST API (localhost:8000)
              |
Authentication + RBAC + Data-Scope Enforcement
              |
Service Layer (14 services)
              |
PostgreSQL / SQLite (single source of truth)
              |
Analytics Engine: Pandas / NumPy / SciPy
              |
Verified Metrics
              |
Gemini 2.5 Flash (narrative only — no number generation)
              |
ReportLab PDF Generator
`

---

## Technology Stack

| Component | Technology |
|---|---|
| API | FastAPI 0.141 + Uvicorn |
| ORM | SQLAlchemy 2.0 |
| Database | PostgreSQL 16 (production) / SQLite (dev) |
| Validation | Pydantic v2 |
| Analytics | Pandas 3, NumPy 2, SciPy 1 |
| Authentication | JWT (python-jose) + bcrypt (passlib) |
| AI Narrative | Google Gemini 2.5 Flash |
| PDF Reports | ReportLab 5 |
| Migrations | Alembic |
| Tests | pytest |
| Frontend | React 19, TypeScript 6, Vite 8, Tailwind CSS |
| Charts | Recharts 3 |

---

## Quick Start (SQLite — Zero Configuration)

`ash
cd project/backend/backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
# Edit .env: update JWT_SECRET_KEY and LLM_API_KEY
uvicorn app.main:app --reload
python seed.py                   # Creates 7 demo accounts
`

Frontend:
`ash
cd project/frontend/result-analysis-agent
npm install
npm run dev
`

Open: http://localhost:5173 — login with seeded credentials.

---

## PostgreSQL Setup (Production)

1. Create database:
`sql
CREATE DATABASE result_analysis;
`

2. Update .env:
`
DATABASE_URL=postgresql+psycopg2://postgres:PASSWORD@localhost:5432/result_analysis
`

3. Run migrations:
`ash
alembic upgrade head
`

4. Seed:
`ash
python seed.py
`

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| DATABASE_URL | SQLAlchemy DB URL | SQLite (dev) |
| FRONTEND_URL | CORS allowed origin | http://localhost:5173 |
| JWT_SECRET_KEY | **Change in production** | dev placeholder |
| JWT_ALGORITHM | JWT algorithm | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | Access token TTL | 30 |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token TTL | 7 |
| TEMP_PASSWORD_EXPIRY_HOURS | Temp password TTL | 24 |
| INTERNAL_MAX | Max internal marks | 30 |
| EXTERNAL_MAX | Max external marks | 70 |
| TOTAL_MAX | Max total marks | 100 |
| GRADE_MAP_JSON | Grade point mapping | O=10, A+=9... |
| LLM_PROVIDER | AI provider | gemini |
| LLM_API_KEY | Gemini API key | (required for AI narrative) |
| LLM_MODEL | Gemini model | gemini-2.5-flash |
| UPLOAD_DIR | File upload storage | uploads |
| REPORT_DIR | PDF report storage | reports |

---

## Authentication Flow

`
PLATFORM_ADMIN creates user
        |
System generates cryptographically secure temporary password (16+ chars)
        |
bcrypt hash stored — plaintext NEVER saved
        |
User logs in → must_change_password: true
        |
Dashboard BLOCKED — redirect to /change-password
        |
User sets permanent password (12+ chars, upper+lower+digit+special)
        |
Temporary credential invalidated
        |
Normal access granted with new JWT
`

---

## RBAC Roles

| Role | Scope | Key Access |
|---|---|---|
| PLATFORM_ADMIN | Full platform | User management, all data, config |
| DEAN | Multi-department | All analytics, reports |
| HOD | Own department only | Upload, analysis, reports |
| FACULTY | Assigned courses/sections | Course/section analytics |
| IQAC | Institution-wide | Analytics, data quality, demographics |
| MANAGEMENT | Aggregated institutional | KPIs, trends, interventions |
| AUDITOR | Read-only | Audit logs, imports, reports |

**Backend enforces all RBAC.** Frontend navigation is UX only.

---

## CSV / Excel Upload Schema

Required columns:

`
roll_number, student_name, programme, department, batch, section,
course_code, course_name, faculty, semester, academic_year,
internal_marks, external_marks, total_marks, grade, grade_point, result_status
`

Optional: gender, category, admission_category, entry_qualification, credits, attempt_number

Result status values: PASS, FAIL, ABSENT, WITHHELD, DEBARRED

---

## Upload Pipeline

`
File upload (CSV / XLSX)
        |
Schema validation (required columns)
        |
Row validation (marks range, grade validity, totals check)
        |
PostgreSQL transaction (Student, Course, Faculty, Result upserts)
        |
ImportBatch created + result_count / student_count populated
        |
Previous active batch deactivated
        |
New batch activated
        |
Frontend refreshes (DatasetContext.triggerRefresh)
        |
All dashboard / analytics queries use new active batch
`

If validation fails: batch NOT activated, previous valid batch stays active.

---

## Active Dataset Mechanism

Every Result row has an import_batch_id. All analytics queries are scoped:

`python
DatasetService.get_active_batch_id()  # returns current ImportBatch.id
# Every service filters: Result.import_batch_id == active_batch_id
`

Multiple uploads cannot mix — each dataset is isolated by batch ID.

---

## API Endpoints

### Authentication
| Method | Path |
|---|---|
| POST | /api/auth/login |
| POST | /api/auth/change-initial-password |
| POST | /api/auth/logout |
| GET | /api/auth/me |
| POST | /api/auth/admin/users |
| GET | /api/auth/admin/users |
| PATCH | /api/auth/admin/users/{id}/deactivate |
| POST | /api/auth/admin/users/{id}/force-reset |
| GET | /api/auth/audit-logs |

### Results
| Method | Path |
|---|---|
| POST | /api/results/upload |
| GET | /api/results/imports |
| GET | /api/results/reconciliation |
| GET | /api/results/data-quality |
| GET | /api/results/dataset-info |

### Analytics
| Method | Path |
|---|---|
| GET | /api/dashboard/summary |
| GET | /api/analysis/summary |
| GET | /api/analysis/grades |
| GET | /api/analysis/courses |
| GET | /api/analysis/sections |
| GET | /api/analysis/faculty |
| GET | /api/analysis/demographics |
| GET | /api/analysis/gpa |
| GET | /api/analysis/merit-list |
| GET | /api/analysis/correlation |
| GET | /api/analysis/historical |
| GET | /api/analysis/interventions |
| GET | /api/analysis/interventions/summary |
| GET | /api/analysis/backlogs |
| GET | /api/analysis/attainment-input |
| POST | /api/analysis/narrative |
| POST | /api/analysis/narrative/generate |

### Reports
| Method | Path |
|---|---|
| POST | /api/reports/generate |
| GET | /api/reports/{id} |
| GET | /api/reports/{id}/download |

---

## Gemini AI Integration

Architecture:
`
PostgreSQL → Pandas Analytics → Verified Metrics → Gemini → Narrative
`

Gemini ONLY generates text narrative. It never calculates:
- Pass percentage, GPA, averages, correlation, ranks, student counts

All numerical analytics use Python/Pandas/SciPy deterministically.

If Gemini is unavailable (quota exceeded, network error, no API key):
- Full analytics continue working
- Deterministic template-based narrative is used
- No feature is blocked

Use POST /api/analysis/narrative/generate to auto-collect current dataset metrics and generate narrative.

---

## Testing

`ash
# All tests (93 core + 20 real-data flow)
pytest tests/ -v

# Specific suites
pytest tests/test_auth.py        # 36 auth/RBAC tests
pytest tests/test_real_data_flow.py  # 20 real-data flow tests
pytest tests/test_upload.py      # Upload tests
pytest tests/test_validation.py  # Validation tests
`

**Test results: 113 tests, 0 failures**

---

## Docker

`ash
docker-compose up --build
# PostgreSQL + FastAPI backend
docker-compose exec backend python seed.py
`

---

## Alembic Migrations

`ash
# Run migrations
alembic upgrade head

# Create new migration after model changes
alembic revision --autogenerate -m "description"

# Check current version
alembic current
`

---

## Troubleshooting

**401 Unauthorized on all endpoints:** Login first via POST /api/auth/login

**403 PASSWORD_CHANGE_REQUIRED:** Call POST /api/auth/change-initial-password

**Dashboard shows no data:** Upload a result dataset via /upload

**bcrypt version warning:** Harmless — passlib cannot read bcrypt.__about__ but works correctly

**Gemini 429 quota exceeded:** Free tier is 20 req/day. System falls back to deterministic narrative automatically

**Swagger UI:** http://localhost:8000/docs

**ReDoc:** http://localhost:8000/redoc
