import { useMemo, useState } from "react";

import type { RiskItem } from "../types";

interface RiskTableProps {
  risks: RiskItem[];
  className?: string;
}

const filters = ["All", "High", "Medium", "Low"] as const;

type SeverityFilter = (typeof filters)[number];

export default function RiskTable({ risks, className = "" }: RiskTableProps) {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("All");
  const sectionClassName = className ? `card surface-card ${className}` : "card surface-card";

  const filteredRisks = useMemo(() => {
    if (severityFilter === "All") {
      return risks;
    }
    return risks.filter((risk) => risk.severity === severityFilter);
  }, [risks, severityFilter]);

  if (risks.length === 0) {
    return (
      <section className={sectionClassName}>
        <div className="card-topline">
          <div>
            <div className="card-caption">Risk Details</div>
            <h3>Risk Details</h3>
          </div>
        </div>
        <p className="muted">No obvious risk was detected, but manual review is still recommended for business logic and edge cases.</p>
      </section>
    );
  }

  return (
    <section className={sectionClassName}>
      <div className="card-topline">
        <div>
          <div className="card-caption">Risk Details</div>
          <h3>Risk Details</h3>
        </div>
        <div className="filter-pills" role="tablist" aria-label="Risk severity filter">
          {filters.map((filter) => (
            <button
              key={filter}
              type="button"
              className={filter === severityFilter ? "filter-pill is-active" : "filter-pill"}
              onClick={() => setSeverityFilter(filter)}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      <div className="table-summary">
        Showing {filteredRisks.length} / {risks.length} risk item(s).
      </div>

      {filteredRisks.length === 0 ? (
        <div className="empty-inline">
          No risks match the current filter. Switch to another severity level to continue.
        </div>
      ) : (
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
                <tr key={`${severityFilter}-${risk.file ?? "pr"}-${risk.type}-${index}`}>
                  <td>
                    <span className={`severity severity-${risk.severity.toLowerCase()}`}>
                      {risk.severity}
                    </span>
                  </td>
                  <td>{risk.confidence}</td>
                  <td>{risk.file ? `${risk.file}${risk.line ? `:${risk.line}` : ""}` : "PR-level"}</td>
                  <td>{risk.type}</td>
                  <td>
                    <code className="evidence-code">{risk.evidence ?? "-"}</code>
                  </td>
                  <td>{risk.suggestion}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
