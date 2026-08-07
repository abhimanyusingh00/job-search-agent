"""Ashby public job-board API — no key required, per-company.
https://api.ashbyhq.com/posting-api/job-board/{company}
"""

from .base import get_json, make_job
from ..company_list import ASHBY_COMPANIES


def fetch():
    jobs = []
    for slug in ASHBY_COMPANIES:
        try:
            data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
        except Exception:
            continue
        for row in data.get("jobs", []):
            jobs.append(make_job(
                source="ashby",
                external_id=row.get("id"),
                company=slug,
                title=row.get("title", ""),
                location=row.get("location", ""),
                description=row.get("descriptionPlain", ""),
                url=row.get("jobUrl", ""),
                posted_at=row.get("publishedAt"),
                remote=row.get("isRemote"),
            ))
    return jobs
