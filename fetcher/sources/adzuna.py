"""Adzuna job search API — free tier, requires app_id/app_key from
https://developer.adzuna.com. Skipped automatically if unset.
"""

import os

from .base import get_json, make_job


def fetch(keywords):
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not app_id or not app_key:
        return []

    country = os.environ.get("ADZUNA_COUNTRY", "us")
    jobs = []
    for keyword in keywords:
        try:
            data = get_json(
                f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": keyword,
                    "max_days_old": 1,
                    "results_per_page": 50,
                    "content-type": "application/json",
                },
            )
        except Exception:
            continue
        for row in data.get("results", []):
            company = (row.get("company") or {}).get("display_name", "")
            location = (row.get("location") or {}).get("display_name", "")
            jobs.append(make_job(
                source="adzuna",
                external_id=row.get("id"),
                company=company,
                title=row.get("title", ""),
                location=location,
                description=row.get("description", ""),
                url=row.get("redirect_url", ""),
                posted_at=row.get("created"),
            ))
    return jobs
