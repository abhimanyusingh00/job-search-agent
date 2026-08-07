import { useState } from "react";
import { resumePdfUrl } from "../api.js";
import ScoreBadge from "./ScoreBadge.jsx";
import SourceTag from "./SourceTag.jsx";

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const [failed, setFailed] = useState(false);

  async function handleClick(e) {
    // currentTarget is only valid during synchronous dispatch — grab it now,
    // it becomes null by the time an awaited catch block runs.
    const button = e.currentTarget;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard permission denied (some browser/embed contexts block it) —
      // fall back to selecting the text so the user can copy manually.
      const range = document.createRange();
      range.selectNodeContents(button.closest(".block-heading").nextElementSibling);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      setFailed(true);
      setTimeout(() => setFailed(false), 2000);
    }
  }

  return (
    <button className="copy-btn" onClick={handleClick}>
      {failed ? (
        "Selected — press ⌘/Ctrl+C"
      ) : copied ? (
        <>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M20 6 9 17l-5-5" />
          </svg>
          Copied
        </>
      ) : (
        <>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="9" y="9" width="13" height="13" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" />
          </svg>
          Copy
        </>
      )}
    </button>
  );
}

export default function ApplicationDetail({ app, onApprove, onReject, onClose }) {
  const [pending, setPending] = useState(null); // "approve" | "reject" | null
  const pdfUrl = resumePdfUrl(app);

  async function handle(action, fn) {
    setPending(action);
    try {
      await fn(app.id);
    } finally {
      setPending(null);
    }
  }

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose} aria-label="Close">&times;</button>

        <div className="detail-header">
          <div>
            <div className="detail-title-line">
              <h2>{app.title}</h2>
              <SourceTag source={app.source} />
            </div>
            <div className="muted">{app.company} — {app.location || "Location n/a"}</div>
            <a className="posting-link" href={app.url} target="_blank" rel="noreferrer">
              View original posting
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M7 17 17 7M9 7h8v8" />
              </svg>
            </a>
          </div>
          <ScoreBadge score={app.ats_score} />
        </div>

        {app.missing_keywords?.length > 0 && (
          <div className="keyword-row">
            <span className="keyword-label">Missing keywords</span>
            <div className="keyword-chips">
              {app.missing_keywords.map((kw) => <span key={kw} className="chip missing">{kw}</span>)}
            </div>
          </div>
        )}
        {app.matched_keywords?.length > 0 && (
          <div className="keyword-row">
            <span className="keyword-label">Matched</span>
            <div className="keyword-chips">
              {app.matched_keywords.map((kw) => <span key={kw} className="chip matched">{kw}</span>)}
            </div>
          </div>
        )}

        <div className="block-heading">
          <h3>Tailored Resume</h3>
          <CopyButton text={app.tailored_resume_text} />
        </div>
        <pre className="text-block">{app.tailored_resume_text}</pre>
        {pdfUrl && (
          <a className="download-link" href={pdfUrl} download>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 3v12m0 0-4-4m4 4 4-4M4 21h16" />
            </svg>
            Download tailored resume PDF
          </a>
        )}

        <div className="block-heading">
          <h3>Cover Letter</h3>
          <CopyButton text={app.cover_letter_text} />
        </div>
        <pre className="text-block">{app.cover_letter_text}</pre>

        {app.status === "pending_review" && (
          <div className="action-row">
            <button
              className="approve-btn" disabled={pending !== null}
              onClick={() => handle("approve", onApprove)}
            >
              {pending === "approve" ? "Approving…" : "Approve — I'll submit this myself"}
            </button>
            <button
              className="reject-btn" disabled={pending !== null}
              onClick={() => handle("reject", onReject)}
            >
              {pending === "reject" ? "Rejecting…" : "Reject"}
            </button>
          </div>
        )}
        {app.status !== "pending_review" && (
          <div className={`status-pill status-${app.status}`}>{app.status.replace("_", " ")}</div>
        )}
      </div>
    </div>
  );
}
