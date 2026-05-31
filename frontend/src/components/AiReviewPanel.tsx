import type { AIReviewResult, AnalysisTrace } from "../types";

interface AiReviewPanelProps {
  aiReview: AIReviewResult | null;
  analysisTrace: AnalysisTrace;
  reviewMode: string;
}

function formatReviewMode(reviewMode: string): string {
  switch (reviewMode) {
    case "rule_based":
      return "规则模式";
    case "ai_assisted":
      return "AI 辅助模式";
    case "ai_fallback":
      return "AI 回退模式";
    default:
      return reviewMode;
  }
}

function renderList(items: string[]) {
  if (!items.length) {
    return <p className="muted">暂无可展示内容。</p>;
  }
  return (
    <ul>
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export default function AiReviewPanel({ aiReview, analysisTrace, reviewMode }: AiReviewPanelProps) {
  const aiFocusFiles = analysisTrace.ai_focus_files?.filter(Boolean) ?? [];

  if (!aiReview) {
    return (
      <section className="card surface-card motion-enter motion-delay-3">
        <h3>AI Review</h3>
        <p className="muted">本次仅使用规则分析结果，尚未启用 AI Reviewer。</p>
      </section>
    );
  }

  return (
    <section className="card surface-card motion-enter motion-delay-3">
      <div className="card-head-row">
        <div>
          <p className="eyebrow">AI Reviewer</p>
          <h3>更像资深 reviewer 的总结与建议</h3>
          <p className="muted">AI 不负责替代规则，而是基于关键上下文补充影响判断、风险解释和修改建议。</p>
        </div>
      </div>

      <div className="ai-meta">
        <span>
          模式: <strong>{formatReviewMode(reviewMode)}</strong>
        </span>
        <span>
          当前状态: <strong>{aiReview.enabled ? "已启用" : "已回退"}</strong>
        </span>
        <span>
          整体风险: <strong>{aiReview.overall_risk_level}</strong>
        </span>
        <span>
          置信度: <strong>{aiReview.confidence}</strong>
        </span>
      </div>

      <div className="explainability-callout">
        <strong>AI 参考上下文：</strong>
        {aiReview.enabled
          ? `本次 AI 共参考 ${analysisTrace.ai_context_file_count ?? 0} 个关键文件，并结合规则命中结果进行总结。`
          : "当前 AI 结果不可用，下面的结论仍可作为规则主导下的快速复核参考。"}
      </div>

      {aiFocusFiles.length ? (
        <div className="focus-file-row">
          {aiFocusFiles.map((filename) => (
            <span key={filename} className="badge">
              {filename}
            </span>
          ))}
        </div>
      ) : null}

      {aiReview.error ? <p className="error-inline">{aiReview.error}</p> : null}

      <div className="ai-block">
        <h4>PR 总结</h4>
        <p>{aiReview.pr_summary || "暂无 AI 总结。"}</p>
      </div>

      <div className="ai-block">
        <h4>主要变更</h4>
        {renderList(aiReview.main_changes)}
      </div>

      <div className="ai-block">
        <h4>风险分析</h4>
        {renderList(aiReview.risk_analysis)}
      </div>

      <div className="ai-block">
        <h4>Review 建议</h4>
        {renderList(aiReview.review_suggestions)}
      </div>
    </section>
  );
}
