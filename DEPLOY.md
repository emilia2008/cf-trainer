# Deploying CF Trainer for free

This guide puts the three parts on free tiers:

| Part | Service | Free tier (October 2026) |
|---|---|---|
| PostgreSQL | [Neon](https://neon.tech) | 0.5 GB storage and 100 compute-hours per project; the database does not expire; compute suspends after 5 minutes idle |
| Backend (FastAPI, Docker) | [Render](https://render.com) web service | 750 instance hours per month; spins down after 15 minutes without traffic and takes about a minute to wake up |
| Frontend (static site) | Render static site | Free; since 1 August 2026 the free (Hobby) workspace includes 5 GB of bandwidth per month, shared by all its services |

Why this split: Render's own free PostgreSQL expires 30 days after creation (then 14 days to
upgrade before deletion), so the database goes to Neon, which does not expire. Free tiers change
often, so check each pricing page before you start.

Storage is not a concern: a stored user takes about 0.1–2 MB (tourist, with 5,491 submissions, is
1.9 MB), so 0.5 GB holds hundreds of users.

You need: this repository on GitHub, and accounts on Neon and Render (signing in with GitHub is
easiest). These are free plans; a provider may still ask for a payment method to verify the account.
This guide never asks you to pick a paid option.

---

## 1. Create the database (Neon)

1. In the Neon console, create a project. Pick the region closest to where you will run the
   backend (for example AWS US East if the Render service is in Virginia, AWS Singapore for Singapore).
2. Open **Connect** and copy the connection string. Use the **direct** connection (not the
   pooled one): the backend keeps its own small connection pool. It looks like
   ```
   postgresql://USER:PASSWORD@ep-xxxx.REGION.aws.neon.tech/neondb?sslmode=require
   ```
   Keep `?sslmode=require`. You do not need to change `postgresql://`: the backend switches it to
   the psycopg 3 driver itself.
3. Nothing else: the backend creates its tables on first start.

## 2. Deploy the backend (Render web service)

1. In Render: **New → Web Service**, connect the GitHub repository.
2. Settings:
   - **Name:** for example `cf-trainer-api` (the URL becomes `https://cf-trainer-api.onrender.com`;
     Render adds a suffix if the name is taken)
   - **Root Directory:** `backend`
   - **Language / Runtime:** `Docker` (it builds `backend/Dockerfile`; the container listens on the
     `$PORT` Render provides)
   - **Instance Type:** `Free`
   - **Health Check Path:** `/api/health` (under Advanced)
3. **Environment variables:**

   | Key | Value |
   |---|---|
   | `DATABASE_URL` | the Neon connection string from step 1 |
   | `CORS_ORIGINS` | leave unset for now; you set it in step 4 |

4. Create the service and wait for the first deploy to finish.
5. Check it: open `https://<your-backend>.onrender.com/api/health` (should show
   `{"status":"ok"}`), then `/docs`, and try **POST /api/users/{handle}/sync** with your own handle,
   then **GET /api/users/{handle}/report**.

Without Docker: choose the **Python** runtime instead, with build command
`pip install -r requirements.txt` and start command
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and set the `PYTHON_VERSION` environment
variable to `3.12.7` (Render's default Python may be newer).

## 3. Deploy the frontend (Render static site)

1. In Render: **New → Static Site**, same repository.
2. Settings:
   - **Name:** for example `cf-trainer`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm ci && npm run build`
   - **Publish Directory:** `dist`
3. **Environment variable:**

   | Key | Value |
   |---|---|
   | `VITE_API_BASE` | `https://<your-backend>.onrender.com` (no trailing slash) |

   Vite bakes this value into the JavaScript at build time. If you change it later, trigger a new
   deploy (**Manual Deploy → Deploy latest commit**).
4. After it is created, open **Redirects/Rewrites** and add a rule so shared links such as
   `/?handle=tourist` and any other path load the app:

   | Source | Destination | Action |
   |---|---|---|
   | `/*` | `/index.html` | Rewrite |

## 4. Connect the two

The frontend and the backend are on different domains, so the browser needs the backend's
permission (CORS) to call it.

1. Copy the frontend URL, for example `https://cf-trainer.onrender.com`.
2. On the backend service, set the environment variable

   | Key | Value |
   |---|---|
   | `CORS_ORIGINS` | `https://cf-trainer.onrender.com` |

   The value must match the browser's address bar exactly: scheme and host, no trailing slash,
   no path. To allow several origins (for example a custom domain as well), separate them with commas.
3. Saving the variable redeploys the backend.

## 5. Check the live app

Open the frontend URL on your phone and analyse your handle. The first request after the
backend has been idle for 15 minutes waits about a minute while Render wakes it up; after that,
a sync takes about 5–10 seconds (three Codeforces calls, two seconds apart) and reports are fast.

Every push to `main` redeploys both services automatically. GitHub Actions runs the tests on the
same push; check the **Actions** tab if a deploy looks wrong.

---

## Environment variables at a glance

| Variable | Set on | Example | Required |
|---|---|---|---|
| `DATABASE_URL` | backend | `postgresql://user:pass@ep-xxxx.aws.neon.tech/neondb?sslmode=require` | yes (otherwise a throwaway SQLite file is used) |
| `CORS_ORIGINS` | backend | `https://cf-trainer.onrender.com` | yes, when the frontend is on another domain |
| `VITE_API_BASE` | frontend, at build time | `https://cf-trainer-api.onrender.com` | yes, when the backend is on another domain |
| `CODEFORCES_MIN_INTERVAL_SECONDS` | backend | `2.0` | no |

## Limits to know about

- **Cold starts.** The free backend sleeps after 15 minutes without traffic. Waking it takes
  about a minute, and the in-memory problem cache starts empty, so the first report after a wake
  also downloads the problem list (a few seconds). An uptime pinger can keep it awake: one service
  running all month uses about 744 of the 750 free hours, so do not keep two free web services
  awake in the same workspace.
- **Neon cold starts.** The database compute suspends after 5 minutes idle; the first query after
  that waits briefly while it resumes. The backend's `pool_pre_ping` replaces connections that
  were dropped while it slept.
- **Shared outbound IPs.** Many Render services share outbound IP addresses, so Codeforces may
  occasionally answer "Call limit exceeded". The client retries twice through its rate limiter;
  if it still fails, the API returns 502 and the user can try again.
- **Bandwidth.** The 5 GB per month is shared by the backend and the static site. A first visit
  downloads about 200 KB (gzip) and a report is about 50 KB, so this covers tens of thousands of
  page views. If traffic grows, move the frontend to Cloudflare Pages (see below), which does not
  meter bandwidth.
- **Data on the free database.** Everything stored can be rebuilt by syncing again, so losing it
  is an inconvenience, not a disaster.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Browser console shows a CORS error | `CORS_ORIGINS` on the backend does not exactly match the frontend origin (check `https`, trailing slash, typos). |
| The app calls `/api/...` on the frontend's own domain and gets 404 | `VITE_API_BASE` was not set when the frontend was built. Set it and redeploy the static site. |
| Opening a shared link gives "Not Found" | The `/*` → `/index.html` rewrite rule is missing on the static site. |
| Backend logs show an SSL or connection error | Use Neon's direct connection string and keep `?sslmode=require`. |
| Every sync returns 502 | Codeforces is down or rate-limiting; check codeforces.com, wait and retry. |

## Other options

- **Frontend on Cloudflare Pages, Netlify or Vercel** instead of Render: the same settings apply
  (root `frontend`, build `npm run build`, output `dist`, variable `VITE_API_BASE`). Cloudflare
  Pages does not meter bandwidth on its free plan, and it serves `index.html` for unknown paths
  when the site has no `404.html`, so no rewrite rule is needed. Vercel's Hobby plan is for
  non-commercial use.
- **Everything on one machine:** any VM with Docker can run `docker compose up -d --build`; the
  nginx container then serves the app and proxies `/api` on the same origin, so neither
  `CORS_ORIGINS` nor `VITE_API_BASE` is needed. Change the PostgreSQL password in
  `docker-compose.yml` first.
