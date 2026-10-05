# CF Trainer

A personal coach for competitive programmers. Enter a Codeforces handle and get a deep analysis of
that one account: where you stand, which topics hold your rating back, what to study, and exactly
which problems to practise next to climb to the next rank.

[![CI](https://github.com/emilia2008/cf-trainer/actions/workflows/ci.yml/badge.svg)](https://github.com/emilia2008/cf-trainer/actions/workflows/ci.yml)

<!-- After deploying (see DEPLOY.md): add the live link, a screenshot and the number of real users. -->

## What the report shows

| Section | Answers |
|---|---|
| **Overview** | Current rank, rating, max rating, points needed for the next rank, problems solved |
| **Rating trend** | Rating history chart, change over the last 5 contests, best gain, worst drop |
| **Difficulty** | Problems solved and tried per rating, your comfort level, and the target range to practise in |
| **Topics** | For every tag: problems solved and tried, first-try acceptance, hardest problem solved |
| **Weak topics** | The 5 tags that matter most at your target level but you rarely solve there, with the reason and study links |
| **Habits** | Verdict breakdown (WA, TLE, RE, MLE, ...) with advice, and how far you usually get in live contests (A, B, C, ...) |
| **Upsolve** | Problems you submitted during a live contest but never got accepted |
| **Recommendations** | 10 unsolved problems in your target range that train your weak topics, linked to Codeforces |

## How the analysis works

All analysis lives in [`backend/app/analysis.py`](backend/app/analysis.py) as pure functions (no
database, no network), so each rule is unit-tested on its own.

- **Distinct problems.** Problems are counted once each, by `contestId + index`, never once per
  submission. The `*special` tag is ignored.
- **Rank.** Codeforces thresholds: Newbie 0, Pupil 1200, Specialist 1400, Expert 1600, Candidate
  Master 1900, Master 2100, International Master 2300, Grandmaster 2400, International Grandmaster
  2600, Legendary Grandmaster 3000. Unrated counts as 0.
- **Comfort rating.** The highest problem rating at which you have solved at least 3 problems.
- **Target range.** `base = max(rating, comfort, 800)` rounded down to a multiple of 100; the range
  is `base + 100` to `base + 300`.
- **Weak topics.** For each tag, `importance` is the share of all Codeforces problems in the target
  range that carry it. Tags with `importance >= 0.05` get
  `score = importance / (1 + solved_in_range)`, where `solved_in_range` is how many problems with that
  tag you solved inside the range. The top 5 by score (ties by tag name) are your weak topics.
- **First try.** A problem counts as solved on the first try when your earliest submission
  (by `creationTimeSeconds`) was accepted. The API lists submissions newest first.
- **Contest level.** Only live participation (`participantType == "CONTESTANT"`). For each problem
  letter, the share of your live contests in which you solved a problem with that letter.
  "You usually solve up to X" is the furthest letter solved in at least half of them.
- **Recommendations.** Unsolved problems rated inside the target range that carry at least one weak
  tag, ranked by number of weak tags matched, then easiest first, then most solved (a proxy for
  problem quality), then problem id.
- **Verdict advice** is shown for every verdict that makes up more than 15% of failed submissions.

## Tech stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2, Pydantic, httpx; SQLite for development,
  PostgreSQL in Docker and production
- **Frontend:** React 19, Vite, Recharts, plain CSS (light and dark themes)
- **Infrastructure:** Docker Compose (PostgreSQL, API, nginx), GitHub Actions CI

## Project structure

```
backend/
  app/
    main.py, config.py, db.py   app setup, settings, database engine
    models.py                   users + one JSON snapshot per user
    schemas.py                  Pydantic models for every API response
    cf_client.py                Codeforces client with a shared rate limiter
    analysis.py                 all analysis (pure functions)
    resources.py                study links per tag, advice per verdict
    services/sync.py            fetch from Codeforces and store
    services/report.py          build the report, 24-hour problem cache
    routes/report.py            HTTP endpoints
  tests/                        pytest, never calls the real Codeforces API
frontend/
  src/App.jsx, src/api.js       page state and API calls
  src/components/               one component per report section
  Dockerfile, nginx.conf        static build served by nginx
docker-compose.yml, .github/workflows/ci.yml
```

## Run locally

Backend (SQLite, no Docker needed):

```bash
cd backend
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload          # API docs at http://localhost:8000/docs
python -m pytest -q                    # run the tests
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev                            # http://localhost:5173 (proxies /api to port 8000)
```

Everything with PostgreSQL instead, if Docker is installed:

```bash
docker compose up --build              # app at http://localhost:8080, API at http://localhost:8000
```

### Configuration

| Variable | Where | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | backend | `sqlite:///./dev.db` | Database. `postgres://` and `postgresql://` URLs are switched to the psycopg 3 driver automatically. |
| `CORS_ORIGINS` | backend | `http://localhost:5173` | Comma-separated frontend origins allowed to call the API. |
| `CODEFORCES_MIN_INTERVAL_SECONDS` | backend | `2.0` | Minimum gap between Codeforces API calls. |
| `VITE_API_BASE` | frontend (build time) | empty | Backend URL. Empty means same origin (Vite proxy in development, nginx in Docker). |

## API

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| POST | `/api/users/{handle}/sync` | Fetch the user's data from Codeforces and store it. `404` unknown handle, `422` malformed handle, `502` Codeforces error. |
| GET | `/api/users/{handle}/report` | Full analysis report. `404` if the handle was never synced, `502` if the problem list cannot be loaded. |

Interactive documentation with every response schema is at `/docs`. Abbreviated report:

```json
{
  "handle": "alice",
  "overview": {"rank": "Pupil", "rating": 1350, "next_rank": "Specialist", "points_to_next": 50, "solved_count": 4},
  "difficulty": {"comfort_rating": null, "target_range": {"lo": 1400, "hi": 1600}, "buckets": [...]},
  "weak_topics": [{"tag": "dp", "importance": 0.8, "solved_in_range": 0, "score": 0.8,
                   "reason": "Appears in 80% of problems rated 1400–1600, and you have not solved any of them yet.",
                   "resources": [{"title": "CP-Algorithms: Introduction to Dynamic Programming", "url": "..."}]}],
  "recommendations": [{"contest_id": 10, "index": "A", "rating": 1400, "matched_tags": ["dp", "math"],
                       "url": "https://codeforces.com/problemset/problem/10/A"}],
  "...": "rating_trend, topics, habits, upsolve"
}
```

## Design notes

**Storage: one JSON snapshot per user.** A sync stores the user's submissions and rating history
as JSON columns (JSONB on PostgreSQL) in a `user_snapshots` table with a unique `user_id`, so a
re-sync updates the row instead of adding a duplicate. The report always reads a user's whole
history at once, and the analysis functions take the API data as is, so normalised tables would
add mapping code without adding a query the app needs. Only the submission fields the analysis
uses are kept, which cuts the stored size to about a third. The trade-off: cross-user SQL queries
(for example "the hardest tag across all users") would need normalised tables added alongside.
All Codeforces calls happen before any write, so a failed sync never leaves half-updated data.

**Rate limit.** Codeforces allows about one API call every two seconds. Every client in the
process shares one `RateLimiter` built on `time.monotonic` and a `threading.Lock`; the lock is
held while waiting, so concurrent requests (FastAPI runs sync routes in a thread pool) queue up and
leave two seconds apart. "Call limit exceeded" responses are retried through the same limiter.
The limit is per process: several server instances would need a shared limiter (for example in
Redis) or a single worker that owns all Codeforces traffic.

**Problem cache.** The full problem list (about 10,000 problems) is needed for every report but
changes rarely, so `ProblemCache` keeps it in memory for 24 hours. The clock is injected through
the constructor, so tests move time forward instead of waiting. The lock is held while
downloading, so concurrent requests on a cold cache trigger one download, not one each. If a
refresh fails while an older copy exists, the old copy is served and the refresh is retried five
minutes later. Each server process has its own copy, and it is lost on restart.

**Limits of the weak-topic score.** `importance / (1 + solved_in_range)` is simple and explainable,
but:

- It only counts solves, not failed attempts, so a tag you tried ten times and never solved scores
  the same as one you never touched.
- Tags are not independent (`dp` and `math` often appear together), so the top 5 can overlap.
- Codeforces tags and ratings are imperfect: tags can be incomplete and new problems have no
  rating, so they are invisible to the analysis.
- The target range follows the definition strictly. A user who has solved a few hard problems in
  practice gets a high comfort rating, so the target can sit far above their contest rating, and
  above about 3300 there are no rated problems in the range at all, so there are no weak topics.
- A Div. 1 problem and its Div. 2 copy have different ids, so one can be recommended after the
  other was solved.

## Tests and CI

`backend/tests` covers the analysis rules, the Codeforces client (`httpx.MockTransport`, fake
clock), the cache, the models and the API (`TestClient` with dependency overrides, in-memory SQLite).
No test calls the real Codeforces API. GitHub Actions runs the backend tests on SQLite and again
on PostgreSQL, builds the frontend, and starts the whole Docker Compose stack for a smoke test.
