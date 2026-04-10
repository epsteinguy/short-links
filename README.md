# Short Links API

URL shortener API built with FastAPI, SQLite/Postgres, JWT admin auth, API keys, click analytics, geolocation, and UTM/referrer tracking.

## Features

- Public redirect endpoint with click tracking
- URL shortening with optional custom short codes
- Bulk URL shortening
- JWT-protected admin analytics endpoints
- API key issuance and revocation for clients
- Click metadata: IP, country, city, device, browser, OS
- Marketing metadata: referrer, UTM source/medium/campaign

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` in project root:

```env
DATABASE_URL=sqlite:///./shortener.db
SECRET_KEY=replace_with_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=2880
BASE_URL=http://localhost:8080
CORS_ORIGINS=*
```

4. Run server:

```bash
python -m uvicorn app.main:app --reload --port 8080
```

5. Open docs: `http://localhost:8080/docs`

## Free Hosting (Recommended): Render

This repository includes `render.yaml` for one-click deploy.

### Option A: Blueprint deploy (recommended)

1. Push this repo to GitHub.
2. Go to Render -> New -> Blueprint.
3. Select this repo.
4. Render creates:
   - a free web service
   - a free Postgres database
5. Update `BASE_URL` env var in Render to your actual Render URL.

### Option B: Manual deploy

1. Create Web Service (Python).
2. Build command:

```bash
pip install -r requirements.txt
```

3. Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

4. Add env vars in Render:

- `DATABASE_URL` -> Postgres connection string
- `SECRET_KEY` -> long random string
- `BASE_URL` -> your app URL
- `CORS_ORIGINS` -> `*` (or your frontend domain)

## Why not Cloudflare Workers?

This backend is Python/FastAPI + SQLAlchemy and not directly runnable on Cloudflare Workers (Workers run JavaScript/TypeScript/Wasm runtimes).

If you still want Cloudflare, you would need a rewrite to Hono/Express-compatible worker style or use Cloudflare Tunnel in front of another host.

## Important Notes

- If you change schema and use SQLite locally, delete `shortener.db` to recreate tables.
- For production, use Postgres and set strict `CORS_ORIGINS`.
- `SECRET_KEY` must be changed from default.

## Main Endpoints

- `POST /shorten` (requires `X-API-Key`)
- `POST /shorten/bulk` (requires `X-API-Key`)
- `GET /{short_code}`
- `POST /admin/register`
- `POST /admin/login`
- `GET /admin/analytics` (JWT)
- `POST /admin/api-keys` (JWT)
