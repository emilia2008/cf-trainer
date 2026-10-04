# CF Trainer

A training dashboard for competitive programmers. Enter a Codeforces handle to see solve statistics by topic, find your weakest topics, and get problem recommendations at the right difficulty. A group leaderboard tracks progress for a club or ICPC team.

<!-- TODO after deploying: live link + "used by N students at UTS" -->

## Features

- Syncs a user's submissions from the Codeforces API (rate-limited, respecting the 1 request / 2 s limit)
- Per-topic statistics: problems solved, attempted, and average rating
- Weak-topic detection and recommendations of unsolved problems near the user's rating
- Weekly leaderboard for a group of users

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, PostgreSQL (SQLite for local development)
- **Frontend:** React + Vite
- **Infrastructure:** Docker Compose, GitHub Actions CI

## Run locally

Backend (SQLite, no Docker needed):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # API docs at http://localhost:8000/docs
python -m pytest -q                    # run tests
```

Frontend (in a second terminal):

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173
```

With PostgreSQL instead: `docker compose up --build`.

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/users/{handle}` | Register a handle and sync its submissions |
| GET | `/api/users/{handle}/stats` | Rating and per-topic statistics |
| GET | `/api/users/{handle}/recommendations` | Problems to practise next |
| GET | `/api/leaderboard` | Users ranked by problems solved this week |

## Design notes

<!-- TODO in your own words: database schema and why, how you handle the API rate limit,
     how you cache the problem list, how you define a "weak" topic. -->
