import type { AIReviewResult } from "../types";

interface AiReviewPanelProps {
  aiReview: AIReviewResult | null;
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
    <ul className="insight-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export default function AiReviewPanel({ aiReview, reviewMode }: AiReviewPanelProps) {
  if (!aiReview) {
    return (
      <section className="card surface-card">
        <div className="card-caption">AI Review</div>
        <h3>AI 审查建议</h3>
        <p className="muted">当前为规则模式，未启用 AI Review。</p>
      </section>
    );
  }

  return (
    <section className="card surface-card">
      <div className="card-topline">
        <div>
          <div className="card-caption">AI Review</div>
          <h3>AI 审查建议</h3>
        </div>
        <div className="workspace-badges">
          <span className="badge badge-outline">{formatReviewMode(reviewMode)}</span>
          <span className="badge badge-outline">Risk: {aiReview.overall_risk_level}</span>
          <span className="badge badge-outline">Confidence: {aiReview.confidence}</span>
        </div>
      </div>

      {aiReview.error ? <p className="error-inline">{aiReview.error}</p> : null}

      <div className="ai-block">
        <h4>PR 总结</h4>
        <p>{aiReview.pr_summary || "暂无 AI 总结"}</p>
      </div>

      <div className="ai-section-grid">
        <div className="ai-block">
          <h4>主要变更</h4>
          {renderList(aiReview.main_changes)}
        </div>

        <div className="ai-block">
          <h4>风险分析</h4>
          {renderList(aiReview.risk_analysis)}
        </div>
      </div>

      <div className="ai-block">
        <h4>Review 建议</h4>
        {renderList(aiReview.review_suggestions)}
      </div>
    </section>
  );
}
