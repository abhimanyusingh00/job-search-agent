import { useEffect, useRef, useState } from "react";
import { getResume, uploadResume } from "../api.js";
import Notice from "./Notice.jsx";

export default function ResumeUpload() {
  const [resume, setResume] = useState(undefined); // undefined = loading
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [replacing, setReplacing] = useState(false);
  const inputRef = useRef(null);

  async function refresh() {
    try {
      setResume(await getResume());
    } catch (err) {
      setError(err.message || String(err));
      setResume(null);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function handleFile(file) {
    if (!file) return;
    if (!/\.(pdf|docx?)$/i.test(file.name)) {
      setError("Please upload a PDF or DOCX file.");
      return;
    }
    setError(null);
    setUploading(true);
    try {
      await uploadResume(file);
      await refresh();
      setReplacing(false);
    } catch (err) {
      setError(err.message || String(err));
    }
    setUploading(false);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files?.[0]);
  }

  const showDropzone = resume === null || replacing;

  return (
    <div className="resume-section">
      {resume === undefined && <div className="muted">Loading…</div>}

      {resume !== undefined && showDropzone && (
        <div
          className={`dropzone ${dragOver ? "drag-over" : ""} ${uploading ? "busy" : ""}`}
          onClick={() => !uploading && inputRef.current?.click()}
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
        >
          <input
            ref={inputRef} type="file" accept=".pdf,.doc,.docx" hidden
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
          {uploading ? (
            <>
              <div className="spinner" />
              <p>Reading your resume and extracting skills…</p>
              <p className="muted small">This can take a few seconds.</p>
            </>
          ) : (
            <>
              <div className="dropzone-icon">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
                  <path d="M14 3v5a1 1 0 0 0 1 1h5" />
                  <path d="M6 3h8l6 6v11a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1Z" />
                  <path d="M12 17v-6M9.5 13.5 12 11l2.5 2.5" />
                </svg>
              </div>
              <p><strong>Click to upload</strong> or drag your resume here</p>
              <p className="muted small">PDF or DOCX</p>
            </>
          )}
        </div>
      )}

      {error && <div className="upload-error"><Notice tone="error">{error}</Notice></div>}

      {resume && !showDropzone && (
        <div className="resume-card">
          <div className="resume-card-header">
            <div>
              <h2>{resume.structured?.contact?.name || resume.filename}</h2>
              <p className="muted">
                {resume.structured?.contact?.email}
                {resume.structured?.contact?.location ? ` — ${resume.structured.contact.location}` : ""}
              </p>
            </div>
            <button className="secondary-btn" onClick={() => setReplacing(true)}>
              Replace resume
            </button>
          </div>

          {resume.structured?.summary && (
            <p className="resume-summary">{resume.structured.summary}</p>
          )}

          {resume.structured?.skills?.length > 0 && (
            <div className="keyword-row">
              <span className="keyword-label">Skills</span>
              <div className="keyword-chips">
                {resume.structured.skills.map((s) => <span key={s} className="chip matched">{s}</span>)}
              </div>
            </div>
          )}

          {resume.structured?.experience?.length > 0 && (
            <div className="resume-experience">
              <span className="keyword-label">Experience</span>
              {resume.structured.experience.map((exp, i) => (
                <div key={i} className="experience-item">
                  <div className="experience-title">
                    {exp.title} <span className="muted">— {exp.company}</span>
                  </div>
                  <div className="muted small">{exp.start} – {exp.end}</div>
                  <ul>
                    {exp.bullets?.map((b, j) => <li key={j}>{b}</li>)}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
