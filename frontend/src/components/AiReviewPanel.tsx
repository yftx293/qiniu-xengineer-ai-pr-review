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
    return <p className="muted">暂无内容</p>;
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
  if (!aiReview) {
    return (
      <section className="card">
        <h3>AI Review</h3>
        <p className="muted">当前为规则模式，未启用 AI Review。</p>
      </section>
    );
  }

  return (
    <section className="card">
      <div className="card-head-row">
        <div>
          <p className="eyebrow">AI Reviewer</p>
          <h3>Reviewer-style summary and suggestions</h3>
        </div>
      </div>

      <div className="ai-meta">
        <span>模式: <strong>{formatReviewMode(reviewMode)}</strong></span>
        <span>启用状态: <strong>{aiReview.enabled ? "已启用" : "已回退"}</strong></span>
        <span>整体风险: <strong>{aiReview.overall_risk_level}</strong></span>
        <span>置信度: <strong>{aiReview.confidence}</strong></span>
      </div>

      <div className="explainability-callout">
        <strong>AI context:</strong>{" "}
        {aiReview.enabled
          ? `本次 AI 参考了 ${analysisTrace.ai_context_file_count ?? 0} 个关键文件，并结合规则扫描结果生成总结。`
          : "AI 结果当前不可用，下面的结论以规则审查结果为主，适合继续做人工快速复核。"}
      </div>

      {aiReview.error ? <p className="error-inline">{aiReview.error}</p> : null}

      <div className="ai-block">
        <h4>PR 总结</h4>
        <p>{aiReview.pr_summary || "暂无 AI 总结"}</p>
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
