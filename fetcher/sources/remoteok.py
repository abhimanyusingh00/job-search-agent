"""RemoteOK public API — no key required. https://remoteok.com/api"""

from datetime import datetime, timezone

from .base import get_json, make_job

API_URL = "https://remoteok.com/api"


def fetch():
    data = get_json(API_URL)
    jobs = []
    for row in data:
        # The first element of the response is a legal/meta notice, not a job.
        if "id" not in row or "position" not in row:
            continue
        epoch = row.get("epoch")
        if epoch:
            posted_at = datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()
        else:
            posted_at = row.get("date")
        jobs.append(make_job(
            source="remoteok",
            external_id=row["id"],
            company=row.get("company", ""),
            title=row.get("position", ""),
            location=row.get("location", ""),
            description=row.get("description", ""),
            url=row.get("url") or row.get("apply_url", ""),
            posted_at=posted_at,
            remote=True,
        ))
    return jobs
