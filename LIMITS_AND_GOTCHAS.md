# Limits & Gotchas (Vercel Hobby + Aiven free Postgres + Google OAuth)

Everything below was true at the time of this migration (2026-07-25). Free-tier terms change — re-check the relevant dashboard if something here seems off.

## Vercel (Hobby / free plan)

- **Function execution timeout.** Hobby-plan serverless functions default to a short timeout (historically 10s, configurable up to a Hobby-tier cap — check **Project Settings → Functions → Function Max Duration** in your Vercel dashboard for the current number, and set `functions.api/index.py.maxDuration` in `vercel.json` to match if you want it explicit). This directly affects:
  - **`POST /api/shipments/bulk/upload`** — loops through the CSV rows sequentially, one Delhivery API call each. A few dozen rows are fine; a few hundred can exceed the timeout and abort mid-batch (rows already processed stay created; the response just never comes back). Split large CSVs into smaller batches.
  - **`GET /api/shipments/bulk/labels`** — fetches one PDF per waybill sequentially before merging. Keep batches to roughly 50-100 waybills at a time on Hobby.
  - If this becomes a real pain, Vercel Pro's higher/configurable timeouts remove the problem entirely — worth a $20/mo upgrade if bulk volume grows.
- **Build treats ESLint warnings as errors.** Vercel sets `CI=true` during builds, and Create React App treats warnings as build-breaking errors under `CI=true`. Two pre-existing warnings (`ShipmentDetail.jsx`, `ShipmentList.jsx`) were fixed as part of this migration so the build succeeds — if you add new `useEffect` hooks later, the same rule applies.
- **Cold starts.** Every Python function invocation after a period of inactivity pays a cold-start cost (SQLAlchemy/Authlib/FastAPI import + engine setup). Expect the first request after idle time to be noticeably slower (typically low hundreds of ms to a couple seconds). Not fixable on Hobby; Pro's "Fluid Compute" reduces this.
- **No cron / background jobs.** The app never had any (shipment status sync happens on-demand inside `GET /api/shipments` and `GET /api/dashboard/stats`, throttled to once per 5 minutes per shipment) — nothing to port, just noting it stays that way. If you ever want scheduled polling independent of user requests, that needs Vercel Cron (a separate feature, not included here).

## Aiven (free Postgres)

- **1 GB storage/RAM, 1 shared CPU, 20 max connections.** Fine for hobby-scale shipment volumes; keep an eye on storage if usage grows. (Supabase is an equally good alternative at 500MB.)
- **20-connection cap, and no managed pooler on the free tier.** Aiven's built-in PgBouncer connection pooling requires the paid Startup plan or higher — not available here. `db/base.py` compensates at the application level instead: a small bounded pool (`pool_size=3, max_overflow=2` → max 5 connections per warm serverless instance) instead of opening one connection per request with no ceiling. This keeps any *single* instance well within budget.
  - **Honest limit of that fix:** it caps connections *per instance*, not across all of them. If Vercel ever spins up many concurrent instances at once (a real traffic spike, not expected at 10-15 clients), total connections could still add up toward 20. If you ever see `too many connections` errors, the real fix is upgrading Aiven to the Startup plan for actual PgBouncer pooling — the app-level pool is a free-tier stopgap, not a substitute for that.
  - `pool_pre_ping=True` is also set, since a connection sitting in the pool can go stale while its serverless instance is frozen between invocations — this transparently checks and reconnects instead of throwing on the next request.
- **Idle services get auto-stopped.** The database (and therefore the whole app) goes unresponsive until you open the Aiven console and restart the service. If this app isn't used daily, expect to do this occasionally. The $5/mo Developer tier removes this if it becomes annoying.
- **`sslmode=require` in Aiven's connection string breaks asyncpg** — must be rewritten to `ssl=true`, or SQLAlchemy throws `TypeError: unexpected keyword argument 'sslmode'` on connect. Worth calling out clearly since it's an easy one to reintroduce if you ever copy-paste a fresh connection string from the Aiven dashboard without editing it.
- **No migration framework.** The app creates its schema with `backend/create_tables.py` — a single `Base.metadata.create_all()` call, no Alembic. If the schema needs to change later, either drop and recreate (dev) or hand-write the couple of `ALTER TABLE` statements needed (production with real data).

## Google OAuth

- **"Testing" publish status caps you at 100 explicitly-added test users.** Fine for a hobby app; if you outgrow it, publishing for general access can trigger Google's app-verification review (not needed for the `email`/`profile` scopes this app uses, but worth knowing).
- **Redirect URI must match exactly** between Google Cloud Console, `GOOGLE_REDIRECT_URI`, and where the app is actually deployed. If you add a custom domain later, add its callback URL to Google's authorized redirect URIs too, or logins will fail with `redirect_uri_mismatch`.

## Things intentionally not covered by this migration

- **No existing production data migration script.** This migration assumes a fresh start on Postgres. If there's live data sitting in the old Mongo instance that needs to carry over, that's a one-time export/import job not included here — flag it if it applies to you.
- **Three test files were left untouched:** `test_delhivery_api.py`, `test_iteration3_fixes.py`, `test_iteration4_features.py`. They don't touch Mongo directly, so the Postgres migration doesn't affect them — but they call protected endpoints (`/api/shipments`, `/api/dashboard/stats`, etc.) with no auth headers at all, expecting `200`. Against the *current* codebase (before or after this migration), those endpoints require auth and would return `401`. This looks like leftover test debt from before auth was added to the app, not something this migration introduced or fixed.
- **Bulk operation batch limits are documentation-only, not enforced in code.** `bulk/upload` and `bulk/labels` don't reject large batches server-side; they just risk timing out on Hobby. Enforcing a hard cap wasn't asked for, so it wasn't added — mentioned here so it doesn't surprise you in production.
