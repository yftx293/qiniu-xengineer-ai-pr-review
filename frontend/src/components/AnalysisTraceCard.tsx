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
      return "AI 审查已完成";
    case "config_missing":
      return "未配置 AI，已回退到规则结果";
    case "fallback_error":
      return "AI 生成失败，已回退到规则结果";
    case "not_requested":
      return "本次未启用 AI";
    default:
      return value || "Unknown";
  }
}

function formatFallbackReason(value: string | null | undefined): string {
  switch (value) {
    case "ai_config_missing":
      return "未配置 AI 模型参数";
    case "ai_generation_failed":
      return "AI 生成失败";
    default:
      return value || "无";
  }
}

export default function AnalysisTraceCard({ analysisTrace }: AnalysisTraceCardProps) {
  const ruleEntries = Object.entries(analysisTrace.rule_hits_by_type);
  const aiFocusFiles = analysisTrace.ai_focus_files?.filter(Boolean) ?? [];

  return (
    <section className="card surface-card motion-enter motion-delay-2">
      <div className="card-head-row">
        <div>
          <p className="eyebrow">Explainability</p>
          <h3>为什么这次结果值得优先看</h3>
          <p className="muted">把上下文来源、规则命中和 AI 参考范围展示出来，方便快速判断本次审查的可信度。</p>
        </div>
      </div>

      <div className="flow-row">
        <span className="flow-step">抓取 PR</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">解析 Diff</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">规则扫描</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">AI 理解</span>
        <span className="flow-arrow">{">"}</span>
        <span className="flow-step">报告输出</span>
      </div>

      <div className="mini-kv-grid">
        <div>
          <span className="k">上下文来源</span>
          <span className="v">{formatContextSource(analysisTrace.context_source)}</span>
        </div>
        <div>
          <span className="k">AI 状态</span>
          <span className="v">{formatAiStatus(analysisTrace.ai_status)}</span>
        </div>
        <div>
          <span className="k">截断文件数</span>
          <span className="v">{analysisTrace.patch_truncated_file_count}</span>
        </div>
        <div>
          <span className="k">规则命中类型</span>
          <span className="v">{ruleEntries.length}</span>
        </div>
        <div>
          <span className="k">AI 参考文件</span>
          <span className="v">{analysisTrace.ai_context_file_count ?? 0}</span>
        </div>
        <div>
          <span className="k">高风险文件</span>
          <span className="v">{analysisTrace.top_risk_file_count ?? 0}</span>
        </div>
      </div>

      <div className="explainability-callout">
        <strong>本次判断逻辑：</strong>{" "}
        {analysisTrace.ai_status === "completed"
          ? `AI 结合 ${analysisTrace.ai_context_file_count ?? 0} 个关键文件与规则命中结果生成总结，因此更适合用来做快速风险定位和 reviewer 视角的复核。`
          : "当前结果以规则引擎输出为主，适合快速定位高确定性风险，再决定是否补充人工深入复核。"}
      </div>

      {analysisTrace.fallback_reason ? (
        <p className="muted">
          回退原因：<strong>{formatFallbackReason(analysisTrace.fallback_reason)}</strong>
        </p>
      ) : null}

      {aiFocusFiles.length ? (
        <div className="rule-hit-list">
          <h4>AI 本次重点关注文件</h4>
          <ul>
            {aiFocusFiles.map((filename) => (
              <li key={filename}>
                <span>{filename}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

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
          <p className="muted">本次没有明确规则命中，结果解释会更多依赖人工复核与 AI 总结。</p>
        )}
      </div>
    </section>
  );
}
