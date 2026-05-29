import type { AIReviewResult } from "../types";

interface AiReviewPanelProps {
  aiReview: AIReviewResult | null;
  reviewMode: string;
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

export default function AiReviewPanel({ aiReview, reviewMode }: AiReviewPanelProps) {
  if (!aiReview) {
    return (
      <section className="card">
        <h3>AI Review</h3>
        <p className="muted">当前为规则模式（rule_based），未启用 AI Review。</p>
      </section>
    );
  }

  return (
    <section className="card">
      <h3>AI Review</h3>
      <div className="ai-meta">
        <span>review_mode: <strong>{reviewMode}</strong></span>
        <span>enabled: <strong>{String(aiReview.enabled)}</strong></span>
        <span>overall_risk_level: <strong>{aiReview.overall_risk_level}</strong></span>
        <span>confidence: <strong>{aiReview.confidence}</strong></span>
      </div>

      {aiReview.error ? <p className="error-inline">{aiReview.error}</p> : null}

      <div className="ai-block">
        <h4>PR Summary</h4>
        <p>{aiReview.pr_summary || "暂无 AI 总结"}</p>
      </div>

      <div className="ai-block">
        <h4>Main Changes</h4>
        {renderList(aiReview.main_changes)}
      </div>

      <div className="ai-block">
        <h4>Risk Analysis</h4>
        {renderList(aiReview.risk_analysis)}
      </div>

      <div className="ai-block">
        <h4>Review Suggestions</h4>
        {renderList(aiReview.review_suggestions)}
      </div>
    </section>
  );
}
