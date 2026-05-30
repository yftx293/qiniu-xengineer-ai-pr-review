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

function formatFallbackReason(value: string | null | undefined): string {
  switch (value) {
    case "ai_config_missing":
      return "AI config missing";
    case "ai_generation_failed":
      return "AI generation failed";
    default:
      return value || "None";
  }
}

export default function AnalysisTraceCard({ analysisTrace }: AnalysisTraceCardProps) {
  const ruleEntries = Object.entries(analysisTrace.rule_hits_by_type);

  return (
    <section className="card">
      <div className="card-head-row">
        <div>
          <p className="eyebrow">Explainability</p>
          <h3>Analysis flow and context coverage</h3>
        </div>
      </div>

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
        <div>
          <span className="k">AI Context Files</span>
          <span className="v">{analysisTrace.ai_context_file_count ?? 0}</span>
        </div>
        <div>
          <span className="k">Top Risk Files</span>
          <span className="v">{analysisTrace.top_risk_file_count ?? 0}</span>
        </div>
      </div>

      <div className="explainability-callout">
        <strong>Why this review:</strong>{" "}
        {analysisTrace.ai_status === "completed"
          ? `AI 基于 ${analysisTrace.ai_context_file_count ?? 0} 个关键文件和规则命中结果生成总结。`
          : "当前结果由规则引擎主导生成，可用于快速定位高确定性风险。"}
      </div>

      {analysisTrace.fallback_reason ? (
        <p className="muted">
          Fallback reason: <strong>{formatFallbackReason(analysisTrace.fallback_reason)}</strong>
        </p>
      ) : null}

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
          <p className="muted">No rule hits in this result. Manual review and AI summary carry more weight here.</p>
        )}
      </div>
    </section>
  );
}
