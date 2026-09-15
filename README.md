# Call Intelligence AI Agent

Post-call intelligence that turns recordings into **evidence-backed** structured notes. Claims are grounded in numbered transcript lines; ambiguous or high-risk items go to a human review queue.

## Stack

- **Backend:** Django, Django REST Framework, Celery, Redis, PostgreSQL
- **Frontend:** React, Vite, TypeScript
- **AI:** OpenAI `gpt-4o-transcribe-diarize` (STT + speakers) + `gpt-4o-mini` (extraction / entailment)
- **Fallback:** Mock providers when `OPENAI_API_KEY` is unset / placeholder (offline demo)

## Architecture

```text
React UI  --REST Token/Session-->  Django/DRF
                                      |
                                      +--> PostgreSQL
                                      +--> Media (recordings)
                                      +--> Celery (eager by default) --> OpenAI
```

Pipeline stages: Upload → Transcribe/Diarize → Extract → Verify evidence → Resolve dates → Compliance → Review items → Sentiment → Complete

## Quick start

### Prerequisites

- Python 3.12+
- Node 20+
- PostgreSQL 16 (database `call_intelligence`)
- Redis (optional if using `CELERY_TASK_ALWAYS_EAGER=True`, the default)

### 1. Environment

```bash
cp .env.example .env
# Edit .env: POSTGRES_USER (often your macOS username), OPENAI_API_KEY
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 8000
```

Demo user: `admin` / `admin1234` (admin — can delete analysis)  
Viewer user: `viewer` / `viewer1234` (can upload + view all; cannot delete/reanalyze)

Passwords come from `.env` (`DEMO_PASSWORD`, `DEMO_VIEWER_PASSWORD`). On deploy, set both in `.env.prod` and run `seed_demo`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### 4. Optional Celery worker

Set `CELERY_TASK_ALWAYS_EAGER=False` in `.env`, then:

```bash
cd backend && source .venv/bin/activate
celery -A config worker -l info
```

## Postman verification

Base URL: `http://127.0.0.1:8000`

1. **Health** — `GET /api/health/` (no auth)
2. **Token** — `POST /api/auth/token/` body `{ "username": "admin", "password": "admin1234" }`
3. Set header `Authorization: Token <token>`
4. **Me** — `GET /api/auth/me/`
5. **Upload** — `POST /api/calls/` multipart: `recording`, `domain=debt_collection`, `call_date=2026-07-01`, optional `title`
6. **List** — `GET /api/calls/`
7. **Detail / transcript / analysis** — `GET /api/calls/{id}/`, `/transcript/`, `/analysis/`
8. **Reviews** — `GET /api/reviews/`, `POST /api/reviews/{id}/decision/` with `{ "decision": "APPROVED", "note": "ok" }`
9. **Search** — `GET /api/search/transcripts/?q=attorney`

Import [`postman/Call_Intelligence.postman_collection.json`](postman/Call_Intelligence.postman_collection.json).

## Deploy (EC2 + Nginx)

For a project/demo deploy on a single EC2 (Docker Compose: Nginx, Gunicorn, Celery, Postgres, Redis), see **[DEPLOY.md](DEPLOY.md)**.

## Tests

```bash
cd backend && source .venv/bin/activate
pytest
```

## Security notes (MVP)

- Calls are scoped to the owning user (UUID guessing returns 404).
- Uploads limited to audio extensions and 25MB.
- Secrets via `.env` only; never commit real API keys.
- Review decisions store reviewer, note, and timestamp.

## Project layout

```text
backend/
  apps/          # accounts, calls, transcripts, intelligence, compliance, reviews, search
  ai/providers/  # OpenAI + mock providers
  config/        # Django settings, Celery, URLs
frontend/        # React app
Implementation Docs/  # PRD, TRD, schema, plan
```

## Libraries added

**Backend:** django, djangorestframework, django-cors-headers, psycopg, celery, redis, django-environ, openai, pydantic, python-dateutil, pytest, pytest-django, ruff, gunicorn

**Frontend:** react, react-dom, react-router-dom, vite, typescript
