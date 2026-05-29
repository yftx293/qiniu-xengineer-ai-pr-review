import { useMemo, useState } from "react";

import type { RiskItem } from "../types";

interface RiskTableProps {
  risks: RiskItem[];
}

type SeverityFilter = "All" | "High" | "Medium" | "Low";

export default function RiskTable({ risks }: RiskTableProps) {
  const [filter, setFilter] = useState<SeverityFilter>("All");

  const filteredRisks = useMemo(() => {
    if (filter === "All") {
      return risks;
    }

    return risks.filter((risk) => risk.severity === filter);
  }, [filter, risks]);

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
      <div className="card-head-row">
        <div>
          <h3>风险详情</h3>
          <p className="muted">支持按风险等级聚焦查看，方便演示时快速定位高优先级问题。</p>
        </div>
        <div className="filter-chips" role="tablist" aria-label="Risk severity filter">
          {(["All", "High", "Medium", "Low"] as SeverityFilter[]).map((severity) => (
            <button
              key={severity}
              type="button"
              className={filter === severity ? "chip chip-active" : "chip"}
              onClick={() => setFilter(severity)}
            >
              {severity === "All" ? "全部" : severity}
            </button>
          ))}
        </div>
      </div>

      <p className="muted">
        当前展示 {filteredRisks.length} / {risks.length} 条风险项。
      </p>

      {!filteredRisks.length ? (
        <section className="inline-empty-state">
          当前筛选条件下没有风险项，可以切换到其他等级继续查看。
        </section>
      ) : null}

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
            {filteredRisks.map((risk, index) => (
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
