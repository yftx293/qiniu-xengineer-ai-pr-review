import type { RiskSummary } from "../types";

interface RiskSummaryCardProps {
  riskSummary: RiskSummary;
  className?: string;
}

export default function RiskSummaryCard({ riskSummary, className = "" }: RiskSummaryCardProps) {
  const sectionClassName = className ? `card surface-card ${className}` : "card surface-card";

  return (
    <section className={sectionClassName}>
      <div className="card-caption">Risk Matrix</div>
      <h3>Risk Overview</h3>

      <div className="summary-grid">
        <div className="summary-tile summary-high">
          <span>High</span>
          <strong>{riskSummary.high}</strong>
        </div>
        <div className="summary-tile summary-medium">
          <span>Medium</span>
          <strong>{riskSummary.medium}</strong>
        </div>
        <div className="summary-tile summary-low">
          <span>Low</span>
          <strong>{riskSummary.low}</strong>
        </div>
        <div className="summary-tile">
          <span>Total</span>
          <strong>{riskSummary.total}</strong>
        </div>
      </div>

      <p className={riskSummary.has_blocking_risk ? "blocking blocking-yes" : "blocking"}>
        {riskSummary.has_blocking_risk
          ? "Blocking risk exists. Review High severity findings first."
          : "No blocking risk was found, but manual review is still recommended."}
      </p>
    </section>
  );
}
