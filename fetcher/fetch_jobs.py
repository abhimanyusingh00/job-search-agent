"""Daily job fetch: pull postings from every free source, keep only ones
first seen in the last 24h that match the target keywords, dedupe, and
upsert into storage.

Run directly: python -m fetcher.fetch_jobs
"""

import os
import re
import sys
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv

from .sources import remoteok, arbeitnow, greenhouse, lever, ashby, adzuna

load_dotenv()

DEFAULT_KEYWORDS = [
    "machine learning", "ml engineer", "ai engineer", "artificial intelligence",
    "data engineer", "mlops", "applied scientist", "ml scientist",
]

SOURCES = [
    ("remoteok", lambda: remoteok.fetch()),
    ("arbeitnow", lambda: arbeitnow.fetch()),
    ("greenhouse", lambda: greenhouse.fetch()),
    ("lever", lambda: lever.fetch()),
    ("ashby", lambda: ashby.fetch()),
]


def get_keywords():
    raw = os.environ.get("JOB_KEYWORDS", "")
    keywords = [k.strip().lower() for k in raw.split(",") if k.strip()]
    return keywords or DEFAULT_KEYWORDS


def fetch_all_raw(keywords):
    """Hits every source. Returns (jobs, errors) — a source failing (network,
    rate limit, etc.) never aborts the others."""
    jobs = []
    errors = []
    for name, fn in SOURCES:
        try:
            jobs.extend(fn())
        except Exception as exc:
            errors.append(f"{name}: {exc}")
    try:
        jobs.extend(adzuna.fetch(keywords))
    except Exception as exc:
        errors.append(f"adzuna: {exc}")
    return jobs, errors


def _keyword_pattern(keyword):
    escaped = re.escape(keyword)
    left = r"\b" if keyword[0].isalnum() else ""
    right = r"\b" if keyword[-1].isalnum() else ""
    return re.compile(left + escaped + right, re.IGNORECASE)


def matches_keywords(job, keywords):
    # Title only, not the full description: AI-native companies' postings all
    # carry "artificial intelligence" style boilerplate in the description
    # regardless of role, which would otherwise match every job at that company.
    title = job["title"]
    return any(_keyword_pattern(kw).search(title) for kw in keywords)


def is_recent(job, since):
    posted_at = job.get("posted_at")
    if not posted_at:
        return False
    try:
        dt = datetime.fromisoformat(posted_at.replace("Z", "+00:00"))
    except ValueError:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt >= since


def filter_recent_and_relevant(jobs, keywords, since):
    return [j for j in jobs if matches_keywords(j, keywords) and is_recent(j, since)]


def dedupe(jobs):
    seen = set()
    unique = []
    for job in jobs:
        key = (job["source"], job["external_id"])
        fallback_key = (job["company"].strip().lower(), job["title"].strip().lower())
        if key in seen or fallback_key in seen:
            continue
        seen.add(key)
        seen.add(fallback_key)
        unique.append(job)
    return unique


def run(now=None, keywords=None, since_hours=24):
    now = now or datetime.now(timezone.utc)
    keywords = keywords or get_keywords()
    since = now - timedelta(hours=since_hours)

    raw_jobs, errors = fetch_all_raw(keywords)
    relevant = filter_recent_and_relevant(raw_jobs, keywords, since)
    unique = dedupe(relevant)

    print(f"Fetched {len(raw_jobs)} raw postings from {len(SOURCES) + 1} sources.")
    if errors:
        print("Source errors (non-fatal):", *errors, sep="\n  - ")
    print(f"{len(relevant)} match keywords + last {since_hours}h; "
          f"{len(unique)} unique after dedupe.")

    from storage import db  # local import: avoids requiring DB deps for pure filtering logic
    inserted = db.upsert_jobs(unique)
    print(f"Upserted {inserted} new/updated rows into storage.")
    return unique


if __name__ == "__main__":
    run()
    sys.exit(0)
