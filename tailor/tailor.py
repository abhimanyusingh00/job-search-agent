"""For every fetched job that hasn't been processed yet: score it against the
base resume for ATS keyword overlap, ask the LLM to tailor the resume bullets
and write a short cover letter, render a PDF, and queue it for review.

Run directly: python -m tailor.tailor
"""

import sys

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import io

from .ats_score import score as ats_score
from .llm import generate_json

TAILOR_SYSTEM_PROMPT = """You tailor a candidate's resume for a specific job posting.
Rules:
- Only use experience, skills, and facts that already appear in the base resume.
  Never invent employers, titles, dates, metrics, or skills the candidate doesn't have.
- You MAY reorder bullets/skills, rephrase wording, and surface relevant existing
  experience more prominently to better match the job description's language and
  the given ATS keyword list.
- If a keyword is missing from the resume entirely, do not claim it — leave it out.
- Keep the resume the same overall length as the input.
- Write a short (150-200 word) cover letter grounded only in the base resume's
  actual experience, referencing the specific company/role.

Output strict JSON: {"tailored_resume_text": "...", "cover_letter_text": "..."}"""


def flatten_resume(structured):
    lines = []
    contact = structured.get("contact", {})
    lines.append(", ".join(v for v in contact.values() if v))
    if structured.get("summary"):
        lines.append("\nSummary:\n" + structured["summary"])
    if structured.get("skills"):
        lines.append("\nSkills: " + ", ".join(structured["skills"]))
    for exp in structured.get("experience", []):
        lines.append(f"\n{exp.get('title', '')} — {exp.get('company', '')} "
                     f"({exp.get('start', '')} - {exp.get('end', '')})")
        for bullet in exp.get("bullets", []):
            lines.append(f"  - {bullet}")
    for edu in structured.get("education", []):
        lines.append(f"\n{edu.get('degree', '')}, {edu.get('school', '')} ({edu.get('end', '')})")
    return "\n".join(lines)


def render_pdf(text):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=LETTER,
                             leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                             topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []
    for para in text.split("\n\n"):
        story.append(Paragraph(para.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 10))
    doc.build(story)
    return buf.getvalue()


def process_job(job, resume_id, base_resume_text):
    ats = ats_score(job.get("description", ""), base_resume_text)

    result = generate_json(
        f"Base resume:\n{base_resume_text}\n\n"
        f"Job posting — {job['title']} at {job['company']}:\n{job.get('description', '')}\n\n"
        f"ATS keywords currently missing from the resume: {', '.join(ats['missing']) or 'none'}",
        system_instruction=TAILOR_SYSTEM_PROMPT,
    )

    pdf_bytes = render_pdf(result["tailored_resume_text"])

    from storage import db
    return db.save_tailored_application(
        job_id=job["id"], resume_id=resume_id,
        tailored_resume_text=result["tailored_resume_text"],
        cover_letter_text=result["cover_letter_text"],
        resume_pdf_bytes=pdf_bytes, ats_score=ats["score"],
        matched_keywords=ats["matched"], missing_keywords=ats["missing"],
    )


def run(limit=None):
    from storage import db

    resume = db.get_latest_resume()
    if not resume:
        print("No resume on file yet. Run: python -m tailor.resume_parser path/to/resume.pdf")
        return

    base_resume_text = flatten_resume(resume["structured"])
    jobs = db.get_jobs_needing_tailoring(limit=limit)
    print(f"{len(jobs)} job(s) need tailoring.")

    processed, failed = 0, 0
    for job in jobs:
        try:
            process_job(job, resume["id"], base_resume_text)
            processed += 1
        except Exception as exc:
            failed += 1
            print(f"  Failed on job {job.get('id')} ({job.get('title')}): {exc}")

    print(f"Tailored {processed} application(s), {failed} failure(s).")


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    run(limit=limit)
