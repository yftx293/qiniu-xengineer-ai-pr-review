import type { AIReviewResult } from "../types";

interface AiReviewPanelProps {
  aiReview: AIReviewResult | null;
  reviewMode: string;
  className?: string;
}

function formatReviewMode(reviewMode: string): string {
  switch (reviewMode) {
    case "rule_based":
      return "Rule based";
    case "ai_assisted":
      return "AI assisted";
    case "ai_fallback":
      return "AI fallback";
    default:
      return reviewMode;
  }
}

function renderList(items: string[]) {
  if (!items.length) {
    return <p className="muted">No content yet.</p>;
  }

  return (
    <ul className="insight-list">
      {items.map((item, index) => (
        <li key={`${item}-${index}`}>{item}</li>
      ))}
    </ul>
  );
}

export default function AiReviewPanel({
  aiReview,
  reviewMode,
  className = "",
}: AiReviewPanelProps) {
  const sectionClassName = className ? `card surface-card ${className}` : "card surface-card";

  if (!aiReview) {
    return (
      <section className={sectionClassName}>
        <div className="card-caption">AI Review</div>
        <h3>AI Review Insights</h3>
        <p className="muted">AI review is disabled. The current result comes from rule analysis only.</p>
      </section>
    );
  }

  return (
    <section className={sectionClassName}>
      <div className="card-topline">
        <div>
          <div className="card-caption">AI Review</div>
          <h3>AI Review Insights</h3>
        </div>
        <div className="workspace-badges">
          <span className="badge badge-outline">{formatReviewMode(reviewMode)}</span>
          <span className="badge badge-outline">Risk: {aiReview.overall_risk_level}</span>
          <span className="badge badge-outline">Confidence: {aiReview.confidence}</span>
        </div>
      </div>

      {aiReview.error ? <p className="error-inline">{aiReview.error}</p> : null}

      <div className="ai-block">
        <h4>PR Summary</h4>
        <p>{aiReview.pr_summary || "No AI summary available."}</p>
      </div>

      <div className="ai-section-grid">
        <div className="ai-block">
          <h4>Main Changes</h4>
          {renderList(aiReview.main_changes)}
        </div>

        <div className="ai-block">
          <h4>Risk Analysis</h4>
          {renderList(aiReview.risk_analysis)}
        </div>
      </div>

      <div className="ai-block">
        <h4>Review Suggestions</h4>
        {renderList(aiReview.review_suggestions)}
      </div>
    </section>
  );
}
