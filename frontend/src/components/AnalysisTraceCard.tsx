import type { AnalysisTrace } from "../types";

interface AnalysisTraceCardProps {
  analysisTrace: AnalysisTrace;
}

function formatContextSource(value: string): string {
  if (value === "github_api_pr_and_files") {
    return "GitHub PR API + Files API";
  }
  return value || "Unknown";
}

function formatAiStatus(value: string): string {
  switch (value) {
    case "completed":
      return "AI review completed";
    case "config_missing":
      return "AI config missing, fallback to rules";
    case "fallback_error":
      return "AI failed, fallback to rules";
    case "not_requested":
      return "AI not requested";
    default:
      return value || "Unknown";
  }
}

export default function AnalysisTraceCard({ analysisTrace }: AnalysisTraceCardProps) {
  const ruleEntries = Object.entries(analysisTrace.rule_hits_by_type);

  return (
    <section className="card">
      <h3>Analysis Flow</h3>
      <div className="flow-row">
        <span className="flow-step">GitHub Fetch</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">Diff Parse</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">Rule Scan</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">AI Summary</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">Markdown Report</span>
      </div>

      <div className="mini-kv-grid">
        <div>
          <span className="k">Context Source</span>
          <span className="v">{formatContextSource(analysisTrace.context_source)}</span>
        </div>
        <div>
          <span className="k">AI Status</span>
          <span className="v">{formatAiStatus(analysisTrace.ai_status)}</span>
        </div>
        <div>
          <span className="k">Patch Truncated Files</span>
          <span className="v">{analysisTrace.patch_truncated_file_count}</span>
        </div>
        <div>
          <span className="k">Rule Types Hit</span>
          <span className="v">{ruleEntries.length}</span>
        </div>
      </div>

      <div className="rule-hit-list">
        <h4>Rule Hit Counts</h4>
        {ruleEntries.length ? (
          <ul>
            {ruleEntries.map(([riskType, count]) => (
              <li key={riskType}>
                <span>{riskType}</span>
                <strong>{count}</strong>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No rule hits in this result. Review depends more on AI summary and manual checks.</p>
        )}
      </div>
    </section>
  );
}
