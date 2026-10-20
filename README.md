# Northstar Learning

A role-based learning platform prototype built with Vue 3, Quasar, Flask, SQLAlchemy, and Neon/PostgreSQL. The frontend and Python API are separate Vercel Services in one deployment; they share the same public origin and `/api` routes.

## Features

- Role-specific admin, instructor, and student workspaces with server-enforced access control.
- Admin account creation, course visibility/locking, and course roster management.
- Instructor-owned course authoring, immutable content revisions, enrollments, and editable AI drafts.
- Student lessons, server-scored quiz attempts, revision-aware score history, and personal learning paths.
- OpenRouter generation using `nvidia/nemotron-3.5-lightning:free`.
- In-memory text extraction for PDF, PPTX, DOCX, and legacy DOC when `antiword` is installed. Original uploads are not retained.

## Requirements

- Python 3.12 or newer.
- Node.js 22.22 or newer recommended (the current tools ran on 22.14 with dependency engine warnings).
- Vercel CLI 62 or newer for the combined local Services runtime.
- A Neon/PostgreSQL URL for persistent data and an OpenRouter API key for AI features.

## Local setup

1. Copy `.env.example` to `.env` only if you do not already have a `.env`; fill in the values locally. Do not commit `.env`.
2. Create and install the backend environment:

   ```powershell
   Push-Location backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements-dev.txt
   ```

3. Run database migrations and create the development-only admin:

   ```powershell
   flask --app app db upgrade
   flask --app app seed-dev-admin
   Pop-Location
   ```

   If `DATABASE_URL` is unset, local development uses an ignored SQLite database under `backend/instance/`. To use Neon locally, set `DATABASE_URL` in `.env` before running migrations.

4. Install frontend packages, then run the backend and frontend in separate terminals:

   ```powershell
   Push-Location frontend
   npm install
   npm run dev
   Pop-Location
   ```

   ```powershell
   Push-Location backend
   $env:DATABASE_URL = 'sqlite:///learning-platform-dev.db'
   .\.venv\Scripts\Activate.ps1
   flask --app app run --host 127.0.0.1 --port 5000
   Pop-Location
   ```

   Open `http://127.0.0.1:5173`. Vite proxies `/api/*` to Flask on port 5000. To exercise the combined Vercel Services router instead, run from the repository root:

   ```powershell
   Copy-Item backend/.venv/Scripts/python.exe backend/.venv/Scripts/python3.exe
   . .\backend\.venv\Scripts\Activate.ps1
   vercel dev --local
   ```

   On Windows the copied `python3.exe` name helps the Vercel Python runtime find the active virtual environment; it is inside the ignored `.venv` folder.

Development sign-in: select **Administrator**, username `admin`, password `password`. The first sign-in requires a password change. This seed is disabled outside development.

For a first production setup, set `INITIAL_ADMIN_USERNAME` and `INITIAL_ADMIN_PASSWORD` (at least 12 characters) as private backend environment variables, then run `flask --app app bootstrap-admin` once. The command refuses to run if any administrator already exists. Remove the bootstrap variables after use.

## Environment variables

- `DATABASE_URL`: Neon/PostgreSQL connection URL. SQLAlchemy uses psycopg 3.
- `SECRET_KEY`: long random secret used to sign session cookies; required in production.
- `OPENROUTER_API_KEY`: server-side API key; never expose it through frontend environment variables.
- `APP_URL`: optional URL sent as OpenRouter request metadata.

For deployment, configure these values in the Vercel project environment settings. The application does not read secrets from frontend build variables.

## Tests and builds

```powershell
Push-Location backend
.\.venv\Scripts\python -m pytest tests
Pop-Location

Push-Location frontend
npm test
npm run build
Pop-Location
```

Backend tests use isolated in-memory SQLite and mocked OpenRouter responses. They do not need Neon credentials or provider requests.

## Upload notes

Files are size-limited to 4 MB to stay below Vercel Functions' 4.5 MB request-body limit, processed in memory, reduced to at most 12,000 characters, and discarded after extraction. Scanned PDFs without selectable text are not OCR'd. Legacy `.doc` files require `antiword`; if it is not available, save the document as `.docx` and upload again.

## Deployment

`vercel.json` defines a Vite frontend service and a Flask Python service. `/api/*` routes to Flask; other paths route to Vue. The local Services configuration has been smoke-tested. Cloud deployment is intentionally not part of the current implementation run. Confirm project authentication, environment variables, Python runtime limits, and the `.doc` parser requirement before the first cloud deployment.
