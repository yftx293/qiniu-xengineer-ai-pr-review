const loadingPhases = [
  "Fetching PR metadata",
  "Parsing changed files",
  "Scanning rule-based risks",
  "Preparing reviewer summary",
];

export default function LoadingState() {
  return (
    <section className="card loading-card" aria-live="polite">
      <div className="loading-scan-line" />
      <div className="loading-wrap">
        <div className="spinner" />
        <div>
          <h3>Analyzing PR</h3>
          <p className="muted">CodeLens is building a structured review from GitHub context, rule scans, and AI assistance.</p>
        </div>
      </div>

      <div className="loading-phase-grid">
        {loadingPhases.map((phase) => (
          <div key={phase} className="loading-phase">
            <span className="loading-dot" />
            <span>{phase}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
