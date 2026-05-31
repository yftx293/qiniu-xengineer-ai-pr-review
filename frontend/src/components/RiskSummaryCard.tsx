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
      <h3>风险概览</h3>

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
          ? "存在阻断级风险，建议优先复核 High 风险项后再决定是否合并。"
          : "当前未看到阻断级风险，但仍建议结合业务上下文继续人工复核。"}
      </p>
    </section>
  );
}
