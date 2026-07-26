# Delhivery Logistics Automation

Multi-tenant dashboard that auto-manifests shipments with Delhivery, tracks them, and manages pickups — for a Delhivery franchise owner running multiple client businesses through one shared API key.

- **Backend:** FastAPI + Postgres (SQLAlchemy async), `backend/`
- **Frontend:** React (CRA + craco) + shadcn/ui, `frontend/`
- **Auth:** Google OAuth (sign-in), with an admin-managed email whitelist per client
- **Deploy target:** Vercel (frontend + Python serverless function, one project)

## Prerequisites

- Python 3.11+
- Node.js + Yarn
- A Postgres database (e.g. Aiven's free tier)
- A Google OAuth client (via Google Cloud Console)
- A Delhivery API key (franchise account)

## Run it locally

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

Create `backend/.env`:

```
DATABASE_URL=postgresql+asyncpg://...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
FRONTEND_URL=http://localhost:3000
SESSION_SECRET_KEY=...                          # python3 -c "import secrets; print(secrets.token_hex(32))"
DELHIVERY_API_KEY=...
DELHIVERY_BASE_URL=https://track.delhivery.com/api
CORS_ORIGINS=http://localhost:3000
```

Create the database tables (one-time, no migration framework needed at this scale):

```bash
python create_tables.py
```

Run the API:

```bash
uvicorn app.main:app --reload --port 8000
```

**Or with Docker Compose** (spins up Postgres + the API together, no local Python/Postgres install needed):

```bash
cd backend
docker compose up --build
docker compose exec api python create_tables.py   # once, first time only
```

The API's `DATABASE_URL` is preset to the compose-managed Postgres container — everything else (`GOOGLE_CLIENT_ID`, etc.) still comes from `backend/.env` as above.

### 2. Frontend

```bash
cd frontend
yarn install
```

Create `frontend/.env`:

```
REACT_APP_BACKEND_URL=http://localhost:8000
```

Run it:

```bash
yarn start
```

Open http://localhost:3000. The first Google account to sign in becomes admin automatically; every account after that must be whitelisted from the Admin page.

## Tests

```bash
cd backend
REACT_APP_BACKEND_URL=http://localhost:8000 DATABASE_URL=... pytest tests/
```

## Deploying

Deploys to Vercel as a single project (frontend static build + Python function, same domain). See [`LIMITS_AND_GOTCHAS.md`](LIMITS_AND_GOTCHAS.md) for free-tier limits and things to watch for.
