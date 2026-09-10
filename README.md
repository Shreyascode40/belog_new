# Digital BE Project Log Book Management System

Production-quality Django REST + PostgreSQL + React/TypeScript for Computer Engineering final-year project workflow.

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py seed
python manage.py runserver 8000
```

Test accounts (password `pass1234`):
- HOD: `hod@college.edu`
- Faculty: `guide1@college.edu` / `guide2@college.edu`
- Reviewer: `reviewer@college.edu`
- Students: `s1@student.edu`, `s2@student.edu`, `s3@student.edu`, `s4@student.edu`

API: `http://localhost:8000/api/v1/`

### Frontend
```bash
cd frontend
npm install
npm run dev # http://localhost:5173
```

### Docker
```bash
docker-compose up --build
```

## Architecture
- See `docs/ER_DIAGRAM.md`, `docs/WORKFLOW_SPEC.md`, `docs/API_SPEC.md`
- JWT auth, RBAC, workflow state machine, audit log, CO/PO attainment

## Roles
- Student: own group, submissions, view marks
- Faculty/Guide: assigned groups, verify/approve, remarks
- Reviewer: assigned reviews, criterion marks
- HOD: full monitoring, assignments, reports, audit

## PDF Generation
- Official replica `Record No. ACA/D/003B Rev 00 DoI 01/02/2025` via `templates/logbook/official.html` + `apps/logbook/services.py`
- Renderer: **WeasyPrint** (primary, Docker: `libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev libcairo2` in Dockerfile) with **reportlab** fallback (pure-Python, works on Windows without GTK). Single code path — no silent fake PDF.
- If both fail: `503 Log book generation is temporarily unavailable, please contact IT/admin` + audit log + notification, never a file containing `Fallback PDF - WeasyPrint not available`.
- Health: `GET /api/v1/logbook/health/` (HOD/admin, checks `%PDF-` magic bytes)
- Regression test: `python manage.py test apps.logbook.tests.LogbookPDFTest` — asserts `%PDF-`, >1KB, text contains project title; runs in CI on same image

## Install Notes (PDF)
- Local Windows: `pip install -r requirements.txt` (weasyprint==70 + xhtml2pdf + pypdf + reportlab) — weasyprint will warn about missing `libgobject` but reportlab fallback ensures real PDF
- Docker/Linux: Dockerfile installs system deps automatically; no manual apt needed

## Workflow States
DRAFT → SUBMITTED → UNDER_REVIEW → APPROVED → LOCKED
                 ↘ CHANGES_REQUIRED → RESUBMITTED → UNDER_REVIEW
