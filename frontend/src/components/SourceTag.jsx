const LABELS = {
  remoteok: "RemoteOK",
  arbeitnow: "Arbeitnow",
  greenhouse: "Greenhouse",
  lever: "Lever",
  ashby: "Ashby",
  adzuna: "Adzuna",
};

export default function SourceTag({ source }) {
  if (!source) return null;
  return <span className="source-tag">{LABELS[source] || source}</span>;
}
