import type { RiskItem } from "../types";

interface RiskTableProps {
  risks: RiskItem[];
}

export default function RiskTable({ risks }: RiskTableProps) {
  if (risks.length === 0) {
    return (
      <section className="card">
        <h3>风险详情</h3>
        <p>未识别到明显风险，但仍建议人工 Review。</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h3>风险详情</h3>
      <div className="table-wrap">
        <table className="risk-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Confidence</th>
              <th>Location</th>
              <th>Type</th>
              <th>Evidence</th>
              <th>Suggestion</th>
            </tr>
          </thead>
          <tbody>
            {risks.map((risk, index) => (
              <tr key={`${risk.file ?? "pr"}-${risk.type}-${index}`}>
                <td><span className={`severity severity-${risk.severity.toLowerCase()}`}>{risk.severity}</span></td>
                <td>{risk.confidence}</td>
                <td>{risk.file ? `${risk.file}${risk.line ? `:${risk.line}` : ""}` : "PR-level"}</td>
                <td>{risk.type}</td>
                <td><code className="evidence-code">{risk.evidence ?? "-"}</code></td>
                <td>{risk.suggestion}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
