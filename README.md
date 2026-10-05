# CF Trainer

A personal coach for competitive programmers. Enter a Codeforces handle and get a deep analysis of the account: where you stand, which topics hold your rating back, what to study, and exactly which problems to practise next to climb to the next rank.

<!-- TODO after deploying: live link + screenshot + "used by N students at UTS" -->

## What the report shows

| Section | Answers |
|---|---|
| **Overview** | Current rank, rating, and points needed for the next rank |
| **Rating trend** | Rating history, recent momentum, best gain and worst drop |
| **Difficulty profile** | Problems solved per rating, your comfort level, and the target range to practise in |
| **Topics** | Solve count, first-try acceptance and hardest solve for every tag |
| **Weak topics** | Tags that appear often at your target level but you rarely solve, with study links |
| **Habits** | Verdict breakdown (WA / TLE / RE) with advice, and how far you usually get in live contests |
| **Upsolve list** | Problems you attempted in contests but never solved |
| **Recommendations** | Unsolved problems in your target range that train your weak topics |

## How the analysis works

- **Target range:** `base + 100` to `base + 300`, where `base` is the higher of your rating and your comfort level (the hardest rating at which you have solved at least 3 problems).
- **Weak topic score:** `importance / (1 + solved_in_range)`, where `importance` is the share of problems in the target range that carry the tag. A tag scores high when it is common at your next level and you have barely solved it there.
- **Recommendations:** unsolved problems in the target range, ranked by how many weak topics they cover, then easiest first, then most solved (a proxy for problem quality).

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
| POST | `/api/users/{handle}/sync` | Fetch and store the user's data from Codeforces |
| GET | `/api/users/{handle}/report` | Full analysis report |

## Design notes

<!-- TODO in your own words: how you store Codeforces data and why, how you respect the
     API rate limit, how you cache the problem list, and the limits of your weak-topic score. -->
