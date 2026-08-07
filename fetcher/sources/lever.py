"""Lever public postings API — no key required, per-company.
https://api.lever.co/v0/postings/{company}?mode=json
"""

from datetime import datetime, timezone

from .base import get_json, make_job
from ..company_list import LEVER_COMPANIES


def fetch():
    jobs = []
    for slug in LEVER_COMPANIES:
        try:
            data = get_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
        except Exception:
            continue
        if not isinstance(data, list):
            continue  # {"ok": false, ...} for unknown/private boards
        for row in data:
            created_at = row.get("createdAt")
            posted_at = (
                datetime.fromtimestamp(created_at / 1000, tz=timezone.utc).isoformat()
                if created_at else None
            )
            categories = row.get("categories") or {}
            jobs.append(make_job(
                source="lever",
                external_id=row.get("id"),
                company=slug,
                title=row.get("text", ""),
                location=categories.get("location", ""),
                description=row.get("descriptionPlain", ""),
                url=row.get("hostedUrl", ""),
                posted_at=posted_at,
                remote="remote" in (categories.get("location", "") or "").lower(),
            ))
    return jobs
