# analytics-platform
A production-ready full-stack analytics platform built with FastAPI and Next.js, featuring RBAC, data visualization, and dashboard persistence.

Analytics Platform is a two-part application:
- `backend/`: FastAPI service providing authentication, analytics APIs, dashboards, and database access.
- `frontend/`: Next.js app that consumes the API and renders the dashboard, login, and import UI.

## Repository structure

- `backend/`
  - `app/`: FastAPI application code
  - `alembic/`: database migration configuration
  - `requirements.txt`: Python dependencies
  - `docker-compose.yml`: optional local Postgres/Redis services
- `frontend/`
  - `src/app/`: Next.js app router pages
  - `src/lib/api.ts`: Axios instance using `NEXT_PUBLIC_API_URL`
  - `package.json`: frontend dependencies and scripts
- `vercel.json`: root rewrite configuration for Vercel monorepo deployment

## Application flow

1. User signs in or signs up from `frontend/src/app/login/page.tsx`.
2. The frontend calls the backend auth endpoints at `NEXT_PUBLIC_API_URL + /api/auth/...`.
3. Backend returns a JWT access token and the frontend stores it in `localStorage`.
4. Frontend uses `src/lib/api.ts` for all API calls, attaching `Authorization: Bearer <token>`.
5. The dashboard page at `src/app/page.tsx` fetches analytics and dashboard data.
6. Protected backend routes validate the token using `backend/app/core/security.py`.

## Required environment keys

### Backend
- `DATABASE_URL`
  - Example: `postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_db`
  - Default fallback in code: `postgresql+asyncpg://postgres:postgres@localhost:5432/analytics_db`

> Note: `backend/app/core/security.py` currently uses a hard-coded `SECRET_KEY`.
> For production, replace `your-super-secret-key-for-assessment-only` with a secure secret or implement env-based secret loading.

### Frontend
- `NEXT_PUBLIC_API_URL`
  - Example local value: `http://localhost:8000/api`
  - Example production value: `https://<your-backend-domain>/api`

## Local development

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the backend service:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Optional local database services:

```powershell
docker compose up -d
```

Run migrations if needed:

```powershell
cd backend
alembic upgrade head
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` and ensure `NEXT_PUBLIC_API_URL` is set for backend communication.

## Deployment notes

### Vercel

If deploying only the frontend, point Vercel to the `frontend` folder as the project root.

- Build command: leave blank, vercel will handle
- Output directory: leave blank for Next.js
- Environment variable: `NEXT_PUBLIC_API_URL=https://<your-backend-domain>/api`

If Vercel is deploying from the repo root, the existing `vercel.json` rewrites requests to `/frontend/$1`. That setup can work only if Vercel is configured to build the nested Next app correctly.

### Backend deployment

The backend is a standard FastAPI app. Ensure the production host has:
- `DATABASE_URL`
- a secure `SECRET_KEY` in `backend/app/core/security.py` or in env-based config
- CORS configured for the frontend origin in `backend/app/main.py`

## Troubleshooting

- 404 on Vercel root route: confirm the project root is `frontend` or that `vercel.json` and build settings are correct.
- API failures: verify `NEXT_PUBLIC_API_URL` points to the backend API, not the frontend URL.
- CORS issues: update `backend/app/main.py` `allow_origins` to include your deployed frontend origin.
- Login / auth issues: the frontend expects `/auth/login`, `/auth/signup`, and `/auth/refresh` on the backend.

## Quick start checklist

- [ ] Backend `DATABASE_URL` set
- [ ] Frontend `NEXT_PUBLIC_API_URL` set
- [ ] Backend CORS allow origin includes frontend host
- [ ] Vercel root path set to `frontend` for frontend-only deployment
- [ ] Secret key replaced for production
