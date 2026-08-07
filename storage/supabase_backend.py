"""Supabase (Postgres + Storage) backend — used in production (GitHub Actions run)
when SUPABASE_URL/SUPABASE_SERVICE_KEY are set. Mirrors storage/local_sqlite.py.
"""

import os

from supabase import create_client

_client = None


def _sb():
    global _client
    if _client is None:
        _client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])
    return _client


def upsert_jobs(jobs):
    if not jobs:
        return 0
    rows = [{
        "source": j["source"], "external_id": j["external_id"], "company": j["company"],
        "title": j["title"], "location": j.get("location"), "description": j.get("description"),
        "url": j["url"], "posted_at": j.get("posted_at"), "remote": j.get("remote"),
    } for j in jobs]
    res = _sb().table("jobs").upsert(rows, on_conflict="source,external_id").execute()
    return len(res.data or [])


def get_jobs_needing_tailoring(limit=None):
    tailored = _sb().table("tailored_applications").select("job_id").execute()
    tailored_ids = {r["job_id"] for r in (tailored.data or [])}
    q = _sb().table("jobs").select("*").order("first_seen_at", desc=True)
    if limit:
        q = q.limit(limit)
    jobs = (q.execute().data) or []
    return [j for j in jobs if j["id"] not in tailored_ids]


def save_resume(filename, raw_text, structured, file_bytes=None):
    file_path = None
    if file_bytes:
        file_path = f"resumes/{filename}"
        _sb().storage.from_("resumes").upload(
            file_path, file_bytes, {"upsert": "true"}
        )
    res = _sb().table("resumes").insert({
        "filename": filename, "raw_text": raw_text, "structured": structured,
        "file_path": file_path,
    }).execute()
    return res.data[0]["id"]


def get_latest_resume():
    res = (_sb().table("resumes").select("*")
           .order("uploaded_at", desc=True).limit(1).execute())
    return res.data[0] if res.data else None


def save_tailored_application(job_id, resume_id, tailored_resume_text, cover_letter_text,
                               resume_pdf_bytes, ats_score, matched_keywords, missing_keywords):
    pdf_path = None
    if resume_pdf_bytes:
        pdf_path = f"tailored/job_{job_id}.pdf"
        _sb().storage.from_("resumes").upload(
            pdf_path, resume_pdf_bytes, {"upsert": "true"}
        )
    res = _sb().table("tailored_applications").upsert({
        "job_id": job_id, "resume_id": resume_id,
        "tailored_resume_text": tailored_resume_text, "cover_letter_text": cover_letter_text,
        "resume_pdf_path": pdf_path, "ats_score": ats_score,
        "matched_keywords": matched_keywords, "missing_keywords": missing_keywords,
    }, on_conflict="job_id,resume_id").execute()
    return res.data[0]["id"]


def list_applications(status=None):
    q = (_sb().table("tailored_applications")
         .select("*, jobs(title, company, url, location, posted_at, source)")
         .order("ats_score", desc=True))
    if status:
        q = q.eq("status", status)
    rows = q.execute().data or []
    for r in rows:
        job = r.pop("jobs", {}) or {}
        r.update(job)
    return rows


def update_application_status(app_id, status):
    _sb().table("tailored_applications").update({"status": status}).eq("id", app_id).execute()
