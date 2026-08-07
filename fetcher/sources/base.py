"""Shared HTTP helpers and the common job-record shape every source normalizes to."""

import requests

HEADERS = {"User-Agent": "job-search-agent (personal use; contact via GitHub)"}
TIMEOUT = 15


def get_json(url, params=None):
    resp = requests.get(url, params=params, headers=HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def make_job(*, source, external_id, company, title, location, description,
             url, posted_at, remote=None):
    """posted_at must be an ISO-8601 UTC string."""
    return {
        "source": source,
        "external_id": str(external_id),
        "company": company,
        "title": title,
        "location": location or "",
        "description": description or "",
        "url": url,
        "posted_at": posted_at,
        "remote": bool(remote) if remote is not None else None,
    }
