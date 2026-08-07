"""Deterministic ATS keyword matching — no LLM call needed. Extracts known
skill/tool terms from a job description and checks which ones appear in the
resume, giving a match score plus the concrete list of missing keywords to
work into the tailored resume.
"""

import re

SKILL_TAXONOMY = [
    # languages
    "python", "sql", "r", "scala", "java", "c++", "julia",
    # ml/dl frameworks
    "pytorch", "tensorflow", "keras", "scikit-learn", "xgboost", "lightgbm",
    "hugging face", "transformers", "jax", "onnx",
    # ml concepts
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "reinforcement learning", "llm", "large language models",
    "generative ai", "genai", "rag", "retrieval augmented generation",
    "fine-tuning", "mlops", "feature engineering", "a/b testing",
    "recommendation systems", "time series", "forecasting", "anomaly detection",
    # data engineering
    "etl", "elt", "airflow", "dbt", "spark", "pyspark", "hadoop", "kafka",
    "snowflake", "redshift", "bigquery", "databricks", "data warehouse",
    "data pipeline", "data modeling", "dagster", "prefect",
    # infra / mlops
    "docker", "kubernetes", "terraform", "ci/cd", "aws", "gcp", "azure",
    "sagemaker", "vertex ai", "mlflow", "kubeflow", "airbyte",
    # data / analytics tools
    "tableau", "power bi", "looker", "pandas", "numpy", "statistics",
    "experimentation", "data visualization",
    # general swe
    "rest api", "microservices", "git", "linux", "agile", "distributed systems",
]


def _pattern(keyword):
    escaped = re.escape(keyword)
    # \b doesn't work around non-word chars like "c++" or "a/b testing" — only
    # anchor a word boundary on the sides that are actually word characters.
    left = r"\b" if keyword[0].isalnum() else ""
    right = r"\b" if keyword[-1].isalnum() else ""
    return re.compile(left + escaped + right, re.IGNORECASE)


_PATTERNS = {kw: _pattern(kw) for kw in SKILL_TAXONOMY}


def extract_keywords(text):
    return sorted({kw for kw, pat in _PATTERNS.items() if pat.search(text)})


def score(job_description, resume_text):
    jd_keywords = extract_keywords(job_description)
    if not jd_keywords:
        return {"score": 0.0, "matched": [], "missing": []}
    matched = [kw for kw in jd_keywords if _PATTERNS[kw].search(resume_text)]
    missing = [kw for kw in jd_keywords if kw not in matched]
    pct = round(100 * len(matched) / len(jd_keywords), 1)
    return {"score": pct, "matched": matched, "missing": missing}
