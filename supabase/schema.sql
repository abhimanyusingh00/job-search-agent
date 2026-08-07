-- Run this once in the Supabase SQL editor (or `supabase db push`) for a new project.

create table if not exists jobs (
    id bigint generated always as identity primary key,
    source text not null,
    external_id text not null,
    company text not null,
    title text not null,
    location text,
    description text,
    url text not null,
    posted_at timestamptz,
    remote boolean,
    first_seen_at timestamptz not null default now(),
    unique (source, external_id)
);

create table if not exists resumes (
    id bigint generated always as identity primary key,
    filename text not null,
    raw_text text not null,
    structured jsonb not null,
    file_path text,
    uploaded_at timestamptz not null default now()
);

create table if not exists tailored_applications (
    id bigint generated always as identity primary key,
    job_id bigint not null references jobs(id) on delete cascade,
    resume_id bigint not null references resumes(id) on delete cascade,
    tailored_resume_text text not null,
    cover_letter_text text not null,
    resume_pdf_path text,
    ats_score numeric not null default 0,
    matched_keywords text[] not null default '{}',
    missing_keywords text[] not null default '{}',
    status text not null default 'pending_review'
        check (status in ('pending_review', 'approved', 'rejected')),
    created_at timestamptz not null default now(),
    unique (job_id, resume_id)
);

create index if not exists idx_jobs_first_seen_at on jobs (first_seen_at desc);
create index if not exists idx_tailored_status on tailored_applications (status);

-- Storage bucket for base resume files + generated tailored PDFs.
insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict (id) do nothing;

-- Row Level Security: this is a single-user personal tool, so the rule is
-- simply "any logged-in Supabase Auth user can read/write everything, nobody
-- else can." Create your one login under Supabase dashboard -> Authentication
-- -> Users -> Add user, and use those credentials in the frontend login form.
-- The daily fetch/tailor scripts use the service_role key (via
-- SUPABASE_SERVICE_KEY), which bypasses RLS entirely, so they're unaffected.
alter table jobs enable row level security;
alter table resumes enable row level security;
alter table tailored_applications enable row level security;

create policy "authenticated read/write jobs" on jobs
    for all using (auth.role() = 'authenticated') with check (auth.role() = 'authenticated');
create policy "authenticated read/write resumes" on resumes
    for all using (auth.role() = 'authenticated') with check (auth.role() = 'authenticated');
create policy "authenticated read/write tailored_applications" on tailored_applications
    for all using (auth.role() = 'authenticated') with check (auth.role() = 'authenticated');

create policy "authenticated access to resumes bucket" on storage.objects
    for all using (bucket_id = 'resumes' and auth.role() = 'authenticated')
    with check (bucket_id = 'resumes' and auth.role() = 'authenticated');
