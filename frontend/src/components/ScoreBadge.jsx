function tier(score) {
  if (score >= 70) return "high";
  if (score >= 40) return "mid";
  return "low";
}

export default function ScoreBadge({ score }) {
  const pct = Math.round(Math.max(0, Math.min(100, score ?? 0)));
  return (
    <div className={`score-badge score-${tier(pct)}`}>
      <svg width="30" height="30" viewBox="0 0 36 36" className="score-ring">
        <circle cx="18" cy="18" r="15.5" fill="none" strokeWidth="3" className="score-ring-bg" />
        <circle
          cx="18" cy="18" r="15.5" fill="none" strokeWidth="3"
          className="score-ring-fg"
          strokeDasharray={`${(pct / 100) * 97.4} 97.4`}
          strokeLinecap="round"
          transform="rotate(-90 18 18)"
        />
      </svg>
      <span>{pct}%</span>
    </div>
  );
}
