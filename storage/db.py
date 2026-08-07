"""Storage backend picker: Supabase in production, local SQLite for dev/testing
when no Supabase credentials are configured. Every function here just proxies
to whichever backend module is active — see local_sqlite.py / supabase_backend.py.
"""

import os

from dotenv import load_dotenv

load_dotenv()

if os.environ.get("SUPABASE_URL") and os.environ.get("SUPABASE_SERVICE_KEY"):
    from . import supabase_backend as _backend
    BACKEND = "supabase"
else:
    from . import local_sqlite as _backend
    BACKEND = "local_sqlite"

upsert_jobs = _backend.upsert_jobs
get_jobs_needing_tailoring = _backend.get_jobs_needing_tailoring
save_resume = _backend.save_resume
get_latest_resume = _backend.get_latest_resume
save_tailored_application = _backend.save_tailored_application
list_applications = _backend.list_applications
update_application_status = _backend.update_application_status
