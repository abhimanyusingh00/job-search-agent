"""Arbeitnow public job board API — no key required.
https://www.arbeitnow.com/api/job-board-api
"""

from datetime import datetime, timezone

from .base import get_json, make_job

API_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch():
    data = get_json(API_URL)
    jobs = []
    for row in data.get("data", []):
        created_at = row.get("created_at")
        posted_at = (
            datetime.fromtimestamp(created_at, tz=timezone.utc).isoformat()
            if created_at else None
        )
        jobs.append(make_job(
            source="arbeitnow",
            external_id=row.get("slug", row.get("url", "")),
            company=row.get("company_name", ""),
            title=row.get("title", ""),
            location=row.get("location", ""),
            description=row.get("description", ""),
            url=row.get("url", ""),
            posted_at=posted_at,
            remote=row.get("remote"),
        ))
    return jobs
