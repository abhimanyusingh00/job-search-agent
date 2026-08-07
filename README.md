# Job Search Agent

Daily-refreshed queue of new ML / AI / Data Engineer job postings, each with an
LLM-tailored resume + cover letter and a deterministic ATS keyword match score,
waiting for you to review and approve — nothing is ever submitted automatically.

Runs entirely on free tiers: GitHub Actions (cron) + Supabase (DB/storage/auth)
+ Gemini API (free tier) + Vercel/Netlify (frontend hosting). No paid hosting,
no scraping of ToS-restricted sites — only public, keyless or free-signup APIs
(RemoteOK, Arbeitnow, Greenhouse, Lever, Ashby, Adzuna).

## How it works

1. `fetcher/fetch_jobs.py` pulls postings from every source, keeps only ones
   whose **title** matches your target keywords (see `JOB_KEYWORDS` below) and
   were first seen in the last 24h, dedupes, and stores them.
2. `tailor/tailor.py` takes your base resume, scores each new job's ATS
   keyword overlap (`tailor/ats_score.py`, no LLM needed), and asks Gemini to
   rewrite resume bullets / write a cover letter grounded only in your real
   experience — never fabricating skills you don't have.
3. The frontend (`frontend/`) shows everything in a review queue, sorted by
   match score. You read the tailored resume/cover letter, and either
   **Approve** (which just means "these materials are ready, I'll go submit
   it myself on the company's site") or **Reject**.

## One-time setup

1. **Supabase** (free): create a project at supabase.com, then in the SQL
   editor run `supabase/schema.sql`. Grab the project URL + `service_role`
   key (Settings → API) for the fetch/tailor scripts, and the `anon` key for
   the frontend. Under Authentication → Users, add yourself as the one login.
2. **Gemini API key** (free): https://aistudio.google.com/apikey
3. **Adzuna** (free, optional — broadens coverage): https://developer.adzuna.com
4. Copy `.env.example` to `.env` and fill in what you have. Leaving
   `SUPABASE_URL`/`SUPABASE_SERVICE_KEY` blank makes everything run against a
   local SQLite file (`storage/data/local.db`) instead — useful for trying
   the pipeline before setting up Supabase.
5. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`

## Running it

```bash
# 1. Pull today's postings
python -m fetcher.fetch_jobs

# 2. Tailor + score every new posting against your resume
python -m tailor.tailor

# 3. Run the local server (needed for resume upload, and for the frontend if
#    Supabase isn't configured yet) — keep this running in its own terminal
python -m scripts.local_server

# 4. Review queue frontend, in another terminal
cd frontend && npm install
# with Supabase configured:
echo "VITE_SUPABASE_URL=...\nVITE_SUPABASE_ANON_KEY=..." > .env
npm run dev
```

Upload your resume from the frontend itself (Resume tab → drag & drop a PDF/DOCX)
— the local server above handles the parsing since it needs `GEMINI_API_KEY`,
which never ships to the browser. CLI alternative: `python -m tailor.resume_parser path/to/resume.pdf`.

## Going live (daily automation)

Push this repo to GitHub, then under Settings → Secrets and variables →
Actions, add: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`,
`ADZUNA_APP_ID`, `ADZUNA_APP_KEY` (secrets), and `ADZUNA_COUNTRY`,
`JOB_KEYWORDS` (variables, optional overrides). The workflow in
`.github/workflows/daily-job-fetch.yml` then runs daily and on-demand
(Actions tab → "Daily job fetch + tailor" → Run workflow).

Deploy `frontend/` to Vercel or Netlify (free tier), setting
`VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY` as its env vars.

## Extending

- **More companies**: add Greenhouse/Lever/Ashby slugs to
  `fetcher/company_list.py`. Bad slugs are skipped automatically.
- **Different target roles**: edit `JOB_KEYWORDS` in `.env` (or the repo
  variable in production) — it's a comma-separated list matched against job
  titles.
- **Better ATS matching**: extend `SKILL_TAXONOMY` in `tailor/ats_score.py`.

## What this deliberately does NOT do

- No scraping of LinkedIn/Indeed/Glassdoor — they prohibit it in their ToS
  and actively block it; only public/free APIs are used.
- No blind auto-submission to employers. "Approve" prepares materials for
  *you* to submit — most ATS apply forms need manual file upload/interaction
  anyway, and this avoids CAPTCHA/ToS problems entirely.
