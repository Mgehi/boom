# Free Postgres Setup

The app needs a plain, internet-reachable Postgres database (Vercel doesn't host databases itself). Recommended: **Aiven's free tier** — genuinely free forever (no credit card, no expiring trial), 1GB storage/RAM, and it's just a standard Postgres instance under the hood, so a normal connection string, no proprietary SQL dialect.

## 1. Create the database

1. Go to https://aiven.io/free-postgresql-database → sign up (free, no card required).
2. Create a project if you don't have one (**Projects** → **Create project**).
3. In the project: **Services** → **Create service** → select **PostgreSQL**.
4. Select the **Free** service tier. (You can't pick a specific cloud/region on the free tier — that's fine at this scale.)
5. Name the service and click **Create service**. Status shows "Rebuilding" during provisioning; wait until it says **Running**.

## 2. Get the connection string

1. Open the service's **Overview** page → click **Quick connect** to see the connection details, or scroll to **Connection information** for the individual fields.
2. Copy the **Service URI**. It looks like:
   ```
   postgres://avnadmin:<password>@<host>.aivencloud.com:<port>/defaultdb?sslmode=require
   ```
3. Turn that into your `DATABASE_URL` with two edits:
   - Scheme prefix → `postgresql+asyncpg://` (the app uses SQLAlchemy's async engine with the `asyncpg` driver)
   - `?sslmode=require` → `?ssl=true` — **this matters**, asyncpg doesn't understand `sslmode` and will throw `TypeError: connect() got an unexpected keyword argument 'sslmode'` if you leave it as-is.
   ```
   postgresql+asyncpg://avnadmin:<password>@<host>.aivencloud.com:<port>/defaultdb?ssl=true
   ```
   That full string is your `DATABASE_URL` — used for both running the app and creating tables.

## 3. Set environment variables and create the tables

```
DATABASE_URL=postgresql+asyncpg://avnadmin:<password>@<host>.aivencloud.com:<port>/defaultdb?ssl=true
```
Set this in Vercel's project Environment Variables, and in your local `backend/.env` for development (you can point local dev at the same Aiven service, or run a local Postgres — either works).

Then create the schema once (no migration framework — just creates the tables from the models):
```
cd backend
DATABASE_URL=postgresql+asyncpg://... python create_tables.py
```

## 4. Free tier limits to know about

- 1 GB storage, 1 GB RAM, 1 shared CPU, **20 max connections** (with no PgBouncer pooling available at this tier — the app compensates with a small bounded connection pool at the application level; see `LIMITS_AND_GOTCHAS.md` for details).
- **Unused/idle services get automatically stopped.** You log back into the Aiven console and restart the service — no data is lost, but a stopped service means your app's requests will fail until you restart it. Same class of gotcha as most free-tier DB hosts; watch for it if this app isn't used daily.
- If you ever want to avoid the auto-stop behavior, Aiven's **Developer tier** starts at $5/mo and keeps the service up continuously, plus more storage (up to 8GB).

Full list of everything to keep in mind (Postgres + Vercel + Google OAuth together) is in `LIMITS_AND_GOTCHAS.md`.

## Alternatives (if you'd rather not use Aiven)

- **Supabase** — also a genuine free-forever tier (500MB storage), also auto-pauses on inactivity (after ~1 week vs Aiven's shorter idle window). Equally good a choice; pick whichever dashboard you prefer.
- **Railway Postgres** — free trial credit, not free forever; becomes paid after the credit runs out.
- **Render Postgres** — free tier databases are deleted after 30 days of inactivity/age, not suitable for a long-lived hobby app.
- **CockroachDB Serverless** — free forever (10 GiB), Postgres wire-compatible, but not literally vanilla Postgres (some SQL/feature differences) — mentioned only as a backup option.
