# AGENTS

## Mandatory Workflow

- Before starting any new task, always read `QWEN.md` first.
- After completing every task, update `QWEN.md` with any new, relevant, and current project knowledge (architecture, commands, constraints, gotchas, and decisions).

## Session Defaults (Repo-Specific)

- Follow `QWEN.md`: respond to users in Russian.
- Treat PostgreSQL on `localhost:5432` (`kufar_monitor`) as production-like data; do not run destructive SQL/migrations there without explicit user confirmation and a backup.
- Safe test DB is `kufar_monitor_test` on `localhost:5433` (`db_test` in Docker).

## What Runs This Repo

- Full stack is expected via `docker-compose up --build` (frontend `:3000`, backend `:8000`, postgres `:5432`, test postgres `:5433`, redis `:6379`).
- Backend entrypoint: `backend/app/main.py` (`uvicorn app.main:app`).
- Frontend entrypoint: `frontend/src/main.tsx`; app wiring/routes live in `frontend/src/app/App.tsx`.

## High-Value Commands

- Frontend (from `frontend/`): `npm ci`, `npm run dev`, `npm run lint`, `npx tsc --noEmit`, `npm run test:unit`, `npm run build`.
- Frontend focused tests: `npm run test:unit -- src/store/favoritesStore.test.ts`, `npm run test:e2e -- tests/e2e/favorites.spec.ts`.
- Backend (from `backend/`): `pip install -r requirements.txt -r requirements-test.txt`, `python -m pytest tests/ -v`.
- Backend focused tests: `python -m pytest tests/test_scan.py -v`, `python -m pytest tests/test_scan.py -k parallel -v`.

## Verification Order (Matches CI Intent)

- Backend: `flake8` -> `black --check` -> `mypy app --ignore-missing-imports` (non-blocking in CI) -> `pytest`.
- Frontend: `npm run lint` -> `npx tsc --noEmit` -> `npm run test:unit:coverage` -> `npm run build`.
- Note: frontend E2E job is disabled in CI (`.github/workflows/ci.yml`); run E2E locally when changing UI flows.

## Testing/Infra Gotchas

- Backend tests assume Postgres test DB; `backend/tests/conftest.py` defaults to `postgresql+asyncpg://postgres:secret@localhost:5433/kufar_monitor_test` when `TEST_DATABASE_URL` is unset.
- Redis is initialized in tests and flushed between tests; keep Redis running for the full backend suite.
- Pytest default addopts in `backend/pyproject.toml` include coverage; use `--no-cov` for faster local loops.

## Migrations and Schema Reality

- Alembic config is in `backend/alembic.ini` with scripts under `backend/app/db/migrations`.
- `backend/app/db/migrations/env.py` uses empty `target_metadata`; do not trust autogenerate output without manual review.
- App startup runs `Listing.metadata.create_all` in `backend/app/main.py`; schema can be created on boot even before explicit migration steps.
