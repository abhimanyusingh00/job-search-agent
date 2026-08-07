"""Extracts text from an uploaded resume (PDF/DOCX) and asks the LLM to
structure it into a consistent JSON shape used everywhere else in the pipeline.

Run directly for a quick check: python -m tailor.resume_parser path/to/resume.pdf
(the UI upload flow — scripts/local_server.py — calls parse_resume_bytes instead)
"""

import io
import json
import sys
from pathlib import Path

import pdfplumber
from docx import Document

from .llm import generate_json

STRUCTURE_SYSTEM_PROMPT = """You turn raw resume text into structured JSON. \
Extract only what is actually present in the text — never invent employers, \
dates, titles, or skills that aren't there. Output must match this shape exactly:

{
  "contact": {"name": "", "email": "", "phone": "", "location": "", "linkedin": ""},
  "summary": "",
  "skills": ["..."],
  "experience": [
    {"company": "", "title": "", "start": "", "end": "", "bullets": ["..."]}
  ],
  "education": [
    {"school": "", "degree": "", "end": ""}
  ]
}"""


def extract_text(source, suffix=None):
    """source: a file path (str/Path), or a file-like object (pass suffix explicitly)."""
    suffix = (suffix or Path(source).suffix).lower()
    if suffix == ".pdf":
        with pdfplumber.open(source) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)
    elif suffix in (".docx", ".doc"):
        doc = Document(source)
        return "\n".join(p.text for p in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported resume format: {suffix}")


def _structure(raw_text):
    if not raw_text.strip():
        raise ValueError("No extractable text found in resume — is it a scanned image PDF?")
    return generate_json(
        f"Resume text:\n\n{raw_text}",
        system_instruction=STRUCTURE_SYSTEM_PROMPT,
    )


def parse_resume(file_path):
    raw_text = extract_text(file_path)
    return raw_text, _structure(raw_text)


def parse_resume_bytes(filename, data):
    raw_text = extract_text(io.BytesIO(data), suffix=Path(filename).suffix)
    return raw_text, _structure(raw_text)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m tailor.resume_parser path/to/resume.pdf")
        sys.exit(1)
    raw_text, structured = parse_resume(sys.argv[1])
    print(json.dumps(structured, indent=2))

    from storage import db
    resume_id = db.save_resume(
        Path(sys.argv[1]).name, raw_text, structured,
        file_bytes=Path(sys.argv[1]).read_bytes(),
    )
    print(f"\nSaved as resume id {resume_id} ({db.BACKEND} backend).")
