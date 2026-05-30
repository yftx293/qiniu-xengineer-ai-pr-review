import { useMemo, useState } from "react";

import type { RiskItem } from "../types";

interface RiskTableProps {
  risks: RiskItem[];
}

type SeverityFilter = "All" | "High" | "Medium" | "Low";

const severityRank: Record<string, number> = {
  High: 0,
  Medium: 1,
  Low: 2,
};

export default function RiskTable({ risks }: RiskTableProps) {
  const [filter, setFilter] = useState<SeverityFilter>("All");

  const sortedRisks = useMemo(
    () =>
      [...risks].sort((left, right) => {
        const severityDiff =
          (severityRank[left.severity] ?? 99) - (severityRank[right.severity] ?? 99);
        if (severityDiff !== 0) {
          return severityDiff;
        }
        return (left.line ?? 0) - (right.line ?? 0);
      }),
    [risks],
  );

  const filteredRisks = useMemo(() => {
    if (filter === "All") {
      return sortedRisks;
    }

    return sortedRisks.filter((risk) => risk.severity === filter);
  }, [filter, sortedRisks]);

  if (risks.length === 0) {
    return (
      <section className="card">
        <h3>风险详情</h3>
        <p>当前未识别到明显风险，但仍建议人工复核关键业务路径和异常处理。</p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="card-head-row">
        <div>
          <p className="eyebrow">Risk Focus</p>
          <h3>聚焦最值得优先复核的问题</h3>
          <p className="muted">默认按 High 到 Low 排序，支持快速聚焦高优先级风险项。</p>
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
