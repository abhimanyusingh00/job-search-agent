import { useEffect, useMemo, useState } from "react";
import { listApplications, updateApplicationStatus, logout, isSupabaseConfigured } from "../api.js";
import ApplicationDetail from "./ApplicationDetail.jsx";
import ScoreBadge from "./ScoreBadge.jsx";
import SourceTag from "./SourceTag.jsx";
import ResumeUpload from "./ResumeUpload.jsx";
import Logo from "./Logo.jsx";
import Notice, { EmptyState } from "./Notice.jsx";

const TABS = [
  { key: "pending_review", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "rejected", label: "Rejected" },
];

export default function ApplicationQueue() {
  const [section, setSection] = useState("applications"); // "applications" | "resume"
  const [tab, setTab] = useState("pending_review");
  const [apps, setApps] = useState([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      setApps(await listApplications(tab));
    } catch (err) {
      setError(err.message || String(err));
    }
    setLoading(false);
  }

  useEffect(() => { if (section === "applications") refresh(); }, [tab, section]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 2600);
    return () => clearTimeout(t);
  }, [toast]);

  useEffect(() => {
    if (!selected) return;
    const onKey = (e) => { if (e.key === "Escape") setSelected(null); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [selected]);

  const filtered = useMemo(() => {
    if (!query.trim()) return apps;
    const q = query.toLowerCase();
    return apps.filter(
      (a) => a.title?.toLowerCase().includes(q) || a.company?.toLowerCase().includes(q)
    );
  }, [apps, query]);

  const avgScore = useMemo(() => {
    if (!apps.length) return null;
    return Math.round(apps.reduce((sum, a) => sum + (a.ats_score || 0), 0) / apps.length);
  }, [apps]);

  async function handleDecision(id, status, jobTitle) {
    await updateApplicationStatus(id, status);
    setSelected(null);
    setToast(status === "approved" ? `Approved — "${jobTitle}" ready to submit` : `Rejected "${jobTitle}"`);
    refresh();
  }

  return (
    <div className="queue-page">
      <header>
        <div className="brand">
          <Logo size={32} />
          <div>
            <h1>Job Search Agent</h1>
            <p className="tagline">Tailored applications, queued for your review</p>
          </div>
        </div>
        <div className="header-right">
          {!isSupabaseConfigured && <span className="dev-badge">local dev mode</span>}
          {isSupabaseConfigured && <button className="link-btn" onClick={logout}>Sign out</button>}
        </div>
      </header>

      <div className="section-toggle">
        <button
          className={section === "applications" ? "section-btn active" : "section-btn"}
          onClick={() => setSection("applications")}
        >
          Applications
        </button>
        <button
          className={section === "resume" ? "section-btn active" : "section-btn"}
          onClick={() => setSection("resume")}
        >
          Resume
        </button>
      </div>

      {section === "resume" && <ResumeUpload />}

      {section === "applications" && (
        <>
          <div className="toolbar">
            <nav className="tabs">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  className={tab === t.key ? "tab active" : "tab"}
                  onClick={() => setTab(t.key)}
                >
                  {t.label}
                </button>
              ))}
            </nav>
            <div className="search-box">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="7" /><path d="m21 21-4.3-4.3" />
              </svg>
              <input
                placeholder="Filter by title or company…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </div>
          </div>

          {!loading && !error && apps.length > 0 && (
            <div className="stats-strip">
              <span><strong>{filtered.length}</strong> of {apps.length} shown</span>
              {avgScore !== null && <span><strong>{avgScore}%</strong> avg ATS match</span>}
            </div>
          )}

          {loading && (
            <div className="app-list">
              {[0, 1, 2].map((i) => <div key={i} className="app-row skeleton" />)}
            </div>
          )}

          {error && <Notice tone="error">Failed to load: {error}</Notice>}

          {!loading && !error && apps.length === 0 && (
            <EmptyState title="Nothing here yet">
              Run <code>python -m fetcher.fetch_jobs</code> then <code>python -m tailor.tailor</code> to populate this queue.
            </EmptyState>
          )}

          {!loading && !error && apps.length > 0 && filtered.length === 0 && (
            <EmptyState title={`No matches for "${query}"`} />
          )}

          <div className="app-list">
            {filtered.map((app) => (
              <button key={app.id} className="app-row" onClick={() => setSelected(app)}>
                <div className="app-row-main">
                  <div className="app-title-line">
                    <span className="app-title">{app.title}</span>
                    <SourceTag source={app.source} />
                  </div>
                  <div className="muted">{app.company} — {app.location || "Location n/a"}</div>
                </div>
                <ScoreBadge score={app.ats_score} />
              </button>
            ))}
          </div>

          {selected && (
            <ApplicationDetail
              app={selected}
              onClose={() => setSelected(null)}
              onApprove={(id) => handleDecision(id, "approved", selected.title)}
              onReject={(id) => handleDecision(id, "rejected", selected.title)}
            />
          )}
        </>
      )}

      {toast && <div className="toast">{toast}</div>}
    </div>
  );
}
