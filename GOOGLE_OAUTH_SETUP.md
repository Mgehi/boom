# Google OAuth Setup (free)

This app now signs users in with Google directly (no third-party auth proxy). You need one OAuth Client ID from Google Cloud — free, no billing account required for basic sign-in.

## 1. Create a Google Cloud project

1. Go to https://console.cloud.google.com/
2. Top-left project dropdown → **New Project** → name it (e.g. `delhivery-logistics`) → **Create**.

## 2. Configure the OAuth consent screen

1. Left sidebar → **APIs & Services** → **OAuth consent screen**.
2. User type: **External** → Create.
3. Fill in: App name, User support email, Developer contact email. Skip scopes (defaults of `openid`, `email`, `profile` are enough — don't add anything else).
4. **Publishing status: leave it in "Testing"**. Testing mode is free forever and needs no Google review, but only the test users you explicitly add can log in.
5. Under **Test users**, add every Gmail address that should be able to sign in (yourself, teammates, whoever you whitelist in the app later). Google caps this at 100 test users — plenty for a hobby project.
   - If you outgrow this later, "Publish" the app for anyone to log in, but that can trigger Google's verification review for certain scopes. Not needed here since we only request `email`/`profile`.

## 3. Create the OAuth Client ID

1. Left sidebar → **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth client ID**.
2. Application type: **Web application**.
3. Name: anything, e.g. `logistics-app-web`.
4. **Authorized JavaScript origins** — add both:
   - `https://<your-vercel-domain>` (e.g. `https://delhivery-logistics.vercel.app`)
   - `http://localhost:3000` (for local frontend dev)
5. **Authorized redirect URIs** — this must exactly match `GOOGLE_REDIRECT_URI` used by the backend:
   - `https://<your-vercel-domain>/api/auth/google/callback`
   - `http://localhost:8000/api/auth/google/callback` (for local backend dev)
6. Click **Create**. Copy the **Client ID** and **Client Secret** shown in the dialog.

## 4. Set environment variables

Add these wherever the backend reads env vars (Vercel project settings → Environment Variables, and your local `backend/.env` for dev):

```
GOOGLE_CLIENT_ID=<client id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<client secret>
GOOGLE_REDIRECT_URI=https://<your-vercel-domain>/api/auth/google/callback
FRONTEND_URL=https://<your-vercel-domain>
SESSION_SECRET_KEY=<any long random string — used to sign the OAuth state cookie>
```

For local dev, use the `localhost` values instead (`GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback`, `FRONTEND_URL=http://localhost:3000`).

Generate a `SESSION_SECRET_KEY` with:
```
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 5. What happens at login

- Frontend "Sign in with Google" button hits `GET /api/auth/google/login`, which redirects to Google's consent screen.
- Google redirects back to `GET /api/auth/google/callback` on the backend with an auth code.
- The backend exchanges the code for the user's email/name/picture, applies the existing admin-bootstrap / email-whitelist rules, creates a session row in Postgres, sets the `session_token` cookie, and redirects to `FRONTEND_URL`.

This is entirely free — Google doesn't charge for OAuth sign-in regardless of user count.
