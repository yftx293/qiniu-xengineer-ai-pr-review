import type { RiskSummary } from "../types";

interface RiskSummaryCardProps {
  riskSummary: RiskSummary;
}

export default function RiskSummaryCard({ riskSummary }: RiskSummaryCardProps) {
  return (
    <section className="card">
      <h3>风险概览</h3>
      <div className="risk-badges">
        <div className="badge badge-high">High: {riskSummary.high}</div>
        <div className="badge badge-medium">Medium: {riskSummary.medium}</div>
        <div className="badge badge-low">Low: {riskSummary.low}</div>
        <div className="badge">Total: {riskSummary.total}</div>
      </div>
      <p className={riskSummary.has_blocking_risk ? "blocking blocking-yes" : "blocking"}>
        {riskSummary.has_blocking_risk ? "存在阻断性风险（建议优先处理）" : "未检测到阻断性风险"}
      </p>
    </section>
  );
}
