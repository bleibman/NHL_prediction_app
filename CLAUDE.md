# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Streamlit (legacy)
streamlit run app.py

# FastAPI backend
uvicorn api.main:app --reload --port 8000

# Next.js frontend (in separate terminal)
cd frontend && npm run dev
```

## ETL & Data Scripts

```bash
# Full ETL pipeline (all 6 steps: teams, seasons, games, playoffs, players, tickets)
python3 scripts/seed.py

# Single season only
python3 scripts/seed.py --season 20242025

# Skip slow games fetch
python3 scripts/seed.py --skip-games

# Daily ticket price snapshot (what GitHub Actions runs)
python3 scripts/fetch_tickets.py

# Import historical attendance from Kaggle CSV
python3 scripts/import_attendance.py data/nhl_games.csv [--dry-run]
```

## Environment Setup

Requires Python 3.12. Copy `.env.example` to `.env` and fill in:
- `SUPABASE_URL` and `SUPABASE_KEY` — required (app crashes without them)
- `SEATGEEK_CLIENT_ID` — optional (ticket features gracefully disabled if missing)

Database tables must be created first by running `db/schema.sql` in the Supabase SQL Editor.

## Architecture

**Data flow:** NHL API / SeatGeek API → `etl/` modules → Supabase (PostgREST) → `api/` routers → Next.js frontend

**Key patterns:**
- `config.py` loads all env vars at import time; Supabase keys raise `RuntimeError` if missing, SeatGeek key is optional
- `db/supabase.py` is the only database access layer — raw PostgREST HTTP calls with batch upsert (500-row chunks). Filter syntax: `{"column": "eq.value"}`
- Each `etl/*.py` module exposes a `fetch_and_upsert_*()` function as its public interface
- `etl/api_client.py` is NHL-specific (shared session, rate limiting, retry). `etl/seatgeek.py` has its own session — do not cross-use them
- `api/` is the FastAPI backend — routers in `api/routers/`, Pydantic schemas in `api/schemas.py`
- `frontend/` is a Next.js 14 app with App Router, Tailwind CSS dark theme, react-plotly.js charts, @tanstack/react-table
- `app.py` is the legacy Streamlit app (kept for reference)
- `ui/theme.py` defines colors, CSS, and `PLOTLY_LAYOUT` dict. `ui/components.py` provides `stat_card()`, `info_box()`, `section_divider()`, `page_header()`, `highlight_card()`, `format_season()`
- Season IDs are 8-digit ints: `20242025` means the 2024-25 season

**ML model:** `models/predictor.py` — GradientBoosting classifier trained on historical playoff series outcomes. Predicts via bracket simulation (5000 iterations).

**Deployment:** Backend on Render (`render.yaml`), frontend on Vercel (root dir: `frontend`). Set `NEXT_PUBLIC_API_URL` on Vercel to the Render service URL.

**Schema conventions (`db/schema.sql`):** Every table uses `IF NOT EXISTS`, enables RLS with a permissive allow-all policy, and grants to `anon, authenticated, service_role`. Serial PKs get sequence grants.

## Pages (in sidebar order)

1. Dashboard — current season standings + top scorers
2. Historical Data — tabbed view across seasons (stats, scorers, playoffs)
3. Predictions — ML bracket simulation with bar chart
4. Ticket Analytics — SeatGeek price cards, upcoming games, trends, team comparison, attendance history
5. Data Refresh — runs ETL pipeline from the UI with progress bar
