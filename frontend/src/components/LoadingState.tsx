import { useEffect, useState } from "react";

const loadingPhases = [
  "Fetching PR context",
  "Parsing diff hunks",
  "Scanning risk rules",
  "Preparing review report",
];

export default function LoadingState() {
  const [phaseIndex, setPhaseIndex] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setPhaseIndex((current) => (current + 1) % loadingPhases.length);
    }, 1100);

    return () => window.clearInterval(timer);
  }, []);

  return (
    <section className="loading-stage motion-enter motion-delay-2" aria-live="polite">
      <div className="loading-status card">
        <div className="loading-beam" aria-hidden="true" />
        <div className="card-caption">Live Analysis</div>
        <h3>CodeLens is analyzing this Pull Request</h3>
        <p>Context is being fetched, diff hunks are being parsed, risks are being scanned, and the final review is being assembled.</p>

        <div className="phase-track" aria-hidden="true">
          {loadingPhases.map((phase, index) => (
            <span
              key={phase}
              className={index === phaseIndex ? "phase-pill is-active" : "phase-pill"}
            >
              {phase}
            </span>
          ))}
        </div>

        <div className="loading-current">
          <div className="spinner" />
          <strong>{loadingPhases[phaseIndex]}</strong>
        </div>
      </div>

      <div className="loading-skeleton-grid">
        <div className="card skeleton-card skeleton-hero" />
        <div className="card skeleton-card skeleton-stat" />
        <div className="card skeleton-card skeleton-stat" />
        <div className="card skeleton-card skeleton-panel" />
      </div>
    </section>
  );
}
