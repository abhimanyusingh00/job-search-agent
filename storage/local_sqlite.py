"""Local SQLite backend — used automatically when SUPABASE_URL/SUPABASE_SERVICE_KEY
are unset, so the pipeline can be developed and tested without a Supabase account.
Mirrors the interface of storage/supabase_backend.py.
"""

import json
import os
import sqlite3
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "local.db"
FILES_DIR = DATA_DIR / "files"

SCHEMA = """
create table if not exists jobs (
    id integer primary key autoincrement,
    source text not null,
    external_id text not null,
    company text not null,
    title text not null,
    location text,
    description text,
    url text not null,
    posted_at text,
    remote integer,
    first_seen_at text not null default (datetime('now')),
    unique (source, external_id)
);

create table if not exists resumes (
    id integer primary key autoincrement,
    filename text not null,
    raw_text text not null,
    structured text not null,
    file_path text,
    uploaded_at text not null default (datetime('now'))
);

create table if not exists tailored_applications (
    id integer primary key autoincrement,
    job_id integer not null references jobs(id),
    resume_id integer not null references resumes(id),
    tailored_resume_text text not null,
    cover_letter_text text not null,
    resume_pdf_path text,
    ats_score real not null default 0,
    matched_keywords text not null default '[]',
    missing_keywords text not null default '[]',
    status text not null default 'pending_review',
    created_at text not null default (datetime('now')),
    unique (job_id, resume_id)
);
"""


def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def upsert_jobs(jobs):
    if not jobs:
        return 0
    conn = _connect()
    count = 0
    with conn:
        for job in jobs:
            cur = conn.execute(
                """insert into jobs (source, external_id, company, title, location,
                       description, url, posted_at, remote)
                   values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                   on conflict(source, external_id) do update set
                       title=excluded.title, description=excluded.description,
                       location=excluded.location, url=excluded.url""",
                (job["source"], job["external_id"], job["company"], job["title"],
                 job.get("location"), job.get("description"), job["url"],
                 job.get("posted_at"), int(bool(job.get("remote")))),
            )
            count += cur.rowcount
    conn.close()
    return count


def get_jobs_needing_tailoring(limit=None):
    conn = _connect()
    q = """select j.* from jobs j
           where not exists (
               select 1 from tailored_applications t where t.job_id = j.id
           )
           order by j.first_seen_at desc"""
    if limit:
        q += f" limit {int(limit)}"
    rows = [dict(r) for r in conn.execute(q).fetchall()]
    conn.close()
    return rows


def save_resume(filename, raw_text, structured, file_bytes=None):
    conn = _connect()
    file_path = None
    if file_bytes:
        file_path = str(FILES_DIR / filename)
        Path(file_path).write_bytes(file_bytes)
    with conn:
        cur = conn.execute(
            "insert into resumes (filename, raw_text, structured, file_path) values (?, ?, ?, ?)",
            (filename, raw_text, json.dumps(structured), file_path),
        )
        resume_id = cur.lastrowid
    conn.close()
    return resume_id


def get_latest_resume():
    conn = _connect()
    row = conn.execute("select * from resumes order by uploaded_at desc limit 1").fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["structured"] = json.loads(d["structured"])
    return d


def save_tailored_application(job_id, resume_id, tailored_resume_text, cover_letter_text,
                               resume_pdf_bytes, ats_score, matched_keywords, missing_keywords):
    conn = _connect()
    pdf_path = None
    if resume_pdf_bytes:
        pdf_path = str(FILES_DIR / f"tailored_resume_job{job_id}.pdf")
        Path(pdf_path).write_bytes(resume_pdf_bytes)
    with conn:
        cur = conn.execute(
            """insert into tailored_applications
                   (job_id, resume_id, tailored_resume_text, cover_letter_text,
                    resume_pdf_path, ats_score, matched_keywords, missing_keywords)
               values (?, ?, ?, ?, ?, ?, ?, ?)
               on conflict(job_id, resume_id) do update set
                   tailored_resume_text=excluded.tailored_resume_text,
                   cover_letter_text=excluded.cover_letter_text,
                   ats_score=excluded.ats_score""",
            (job_id, resume_id, tailored_resume_text, cover_letter_text, pdf_path,
             ats_score, json.dumps(matched_keywords), json.dumps(missing_keywords)),
        )
        app_id = cur.lastrowid
    conn.close()
    return app_id


def list_applications(status=None):
    conn = _connect()
    q = """select t.*, j.title, j.company, j.url, j.location, j.posted_at, j.source
           from tailored_applications t join jobs j on j.id = t.job_id"""
    params = ()
    if status:
        q += " where t.status = ?"
        params = (status,)
    q += " order by t.ats_score desc"
    rows = [dict(r) for r in conn.execute(q, params).fetchall()]
    conn.close()
    for r in rows:
        r["matched_keywords"] = json.loads(r["matched_keywords"])
        r["missing_keywords"] = json.loads(r["missing_keywords"])
    return rows


def update_application_status(app_id, status):
    conn = _connect()
    with conn:
        conn.execute("update tailored_applications set status = ? where id = ?", (status, app_id))
    conn.close()
