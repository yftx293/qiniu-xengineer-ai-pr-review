import type { RiskSummary } from "../types";

interface RiskSummaryCardProps {
  riskSummary: RiskSummary;
}

export default function RiskSummaryCard({ riskSummary }: RiskSummaryCardProps) {
  return (
    <section className="card surface-card">
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
          ? "存在阻断性风险，建议优先复查 High severity 项。"
          : "当前没有阻断性风险，但仍建议结合业务上下文做人工复核。"}
      </p>
    </section>
  );
}
