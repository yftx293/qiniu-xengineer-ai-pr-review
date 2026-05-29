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
      return "AI 已完成分析";
    case "config_missing":
      return "AI 未配置，已回退到规则模式";
    case "fallback_error":
      return "AI 调用失败，已回退到规则模式";
    case "not_requested":
      return "未启用 AI";
    default:
      return value || "Unknown";
  }
}

export default function AnalysisTraceCard({ analysisTrace }: AnalysisTraceCardProps) {
  const ruleEntries = Object.entries(analysisTrace.rule_hits_by_type);

  return (
    <section className="card">
      <h3>分析链路</h3>
      <div className="flow-row">
        <span className="flow-step">GitHub 获取</span>
        <span className="flow-arrow">→</span>
        <span className="flow-step">Diff 解析</span>
        <span className="flow-arrow">→</span>
        <span className="flow-step">规则识别</span>
        <span className="flow-arrow">→</span>
        <span className="flow-step">AI 总结</span>
        <span className="flow-arrow">→</span>
        <span className="flow-step">Markdown 报告</span>
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
        <h4>规则命中统计</h4>
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
          <p className="muted">当前未命中规则风险，结果更依赖人工复核与 AI 总结。</p>
        )}
      </div>
    </section>
  );
}
