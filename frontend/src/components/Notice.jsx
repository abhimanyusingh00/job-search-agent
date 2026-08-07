const ICONS = {
  error: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" /><path d="M12 8v5M12 16h.01" />
    </svg>
  ),
  info: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="9" /><path d="M12 16v-5M12 8h.01" />
    </svg>
  ),
  empty: (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M3 7h18M3 7v11a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V7M3 7l3-4h12l3 4M9 12h6" />
    </svg>
  ),
};

export default function Notice({ tone = "info", children }) {
  return (
    <div className={`notice notice-${tone}`}>
      <span className="notice-icon">{ICONS[tone]}</span>
      <div className="notice-body">{children}</div>
    </div>
  );
}

export function EmptyState({ title, children }) {
  return (
    <div className="empty-state">
      <span className="empty-icon">{ICONS.empty}</span>
      <p className="empty-title">{title}</p>
      {children && <div className="muted small">{children}</div>}
    </div>
  );
}
