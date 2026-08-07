"""Greenhouse public job-board API — no key required, per-company.
https://boards-api.greenhouse.io/v1/boards/{company}/jobs
"""

from .base import get_json, make_job
from ..company_list import GREENHOUSE_COMPANIES


def fetch():
    jobs = []
    for slug in GREENHOUSE_COMPANIES:
        try:
            data = get_json(
                f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs",
                params={"content": "true"},
            )
        except Exception:
            continue  # company doesn't use Greenhouse under this slug, or board is private
        for row in data.get("jobs", []):
            posted_at = row.get("first_published") or row.get("updated_at")
            location = (row.get("location") or {}).get("name", "")
            jobs.append(make_job(
                source="greenhouse",
                external_id=row.get("id"),
                company=row.get("company_name", slug),
                title=row.get("title", ""),
                location=location,
                description=row.get("content", ""),
                url=row.get("absolute_url", ""),
                posted_at=posted_at,
            ))
    return jobs
