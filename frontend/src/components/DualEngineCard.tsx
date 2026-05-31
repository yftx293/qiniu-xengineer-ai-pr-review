import type { AIReviewResult, AnalysisTrace, RiskSummary } from "../types";

interface DualEngineCardProps {
  aiReview: AIReviewResult | null;
  analysisTrace: AnalysisTrace;
  riskSummary: RiskSummary;
  reviewMode: string;
}

function getModeLabel(reviewMode: string): string {
  switch (reviewMode) {
    case "ai_assisted":
      return "AI Assisted";
    case "ai_fallback":
      return "AI Fallback";
    case "rule_based":
      return "Rule Based";
    default:
      return reviewMode || "Unknown";
  }
}

export default function DualEngineCard({
  aiReview,
  analysisTrace,
  riskSummary,
  reviewMode,
}: DualEngineCardProps) {
  const aiContextCount = analysisTrace.ai_context_file_count ?? 0;
  const topRiskFileCount = analysisTrace.top_risk_file_count ?? 0;
  const patchTruncatedCount = analysisTrace.patch_truncated_file_count ?? 0;
  const ruleHitTypes = Object.keys(analysisTrace.rule_hits_by_type).length;

  return (
    <section className="card dual-engine-card motion-enter motion-delay-2">
      <div className="dual-engine-head">
        <div>
          <p className="eyebrow">Dual Engine Review</p>
          <h3>为什么这不是普通大模型问答</h3>
          <p className="muted">
            CodeLens 先用规则引擎抓高确定性风险，再让 AI Reviewer 在关键上下文上做归纳和建议，因此结果更适合真实 PR
            审查场景。
          </p>
        </div>
        <div className="badge-stack">
          <span className="badge badge-contrast">{getModeLabel(reviewMode)}</span>
          <span className="badge">{patchTruncatedCount > 0 ? "Partial Context" : "Full Context"}</span>
        </div>
      </div>

      <div className="dual-engine-grid">
        <article className="engine-panel">
          <p className="engine-label">Rule Engine</p>
          <h4>负责高确定性风险定位</h4>
          <ul className="engine-list">
            <li>规则命中类型: {ruleHitTypes}</li>
            <li>高风险项: {riskSummary.high}</li>
            <li>高风险文件: {topRiskFileCount}</li>
          </ul>
        </article>

        <article className="engine-panel engine-panel-ai">
          <p className="engine-label">AI Reviewer</p>
          <h4>负责上下文理解与审查话术</h4>
          <ul className="engine-list">
            <li>参考文件数: {aiContextCount}</li>
            <li>AI 状态: {analysisTrace.ai_status}</li>
            <li>整体风险: {aiReview?.overall_risk_level ?? "Rule-led"}</li>
          </ul>
        </article>
      </div>

      {analysisTrace.fallback_reason ? (
        <p className="fallback-note">
          当前已回退到规则分析路径，原因: <strong>{analysisTrace.fallback_reason}</strong>。结果仍适合用来做快速人工复核。
        </p>
      ) : null}
    </section>
  );
}
