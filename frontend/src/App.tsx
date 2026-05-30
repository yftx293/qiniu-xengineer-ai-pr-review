import { useMemo, useState } from "react";

import { analyzePullRequest } from "./api";
import type { ReviewResponse } from "./types";
import ReviewForm from "./components/ReviewForm";
import PrInfoCard from "./components/PrInfoCard";
import RiskSummaryCard from "./components/RiskSummaryCard";
import RiskTable from "./components/RiskTable";
import AiReviewPanel from "./components/AiReviewPanel";
import MarkdownReport from "./components/MarkdownReport";
import LoadingState from "./components/LoadingState";
import ErrorBanner from "./components/ErrorBanner";
import AnalysisTraceCard from "./components/AnalysisTraceCard";

function formatReviewMode(reviewMode: string): string {
  switch (reviewMode) {
    case "rule_based":
      return "Rule Based";
    case "ai_assisted":
      return "AI Assisted";
    case "ai_fallback":
      return "AI Fallback";
    default:
      return reviewMode || "Unknown";
  }
}

function getAiStatusLabel(status: string): string {
  switch (status) {
    case "completed":
      return "AI Completed";
    case "config_missing":
      return "Fallback: Missing Config";
    case "fallback_error":
      return "Fallback: Request Error";
    case "not_requested":
      return "AI Disabled";
    default:
      return status || "Unknown";
  }
}

export default function App() {
  const [prUrl, setPrUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [resultSequence, setResultSequence] = useState(0);
  const [isResetting, setIsResetting] = useState(false);

  const hasResult = useMemo(() => result !== null, [result]);
  const ruleTypeCount = result ? Object.keys(result.analysis_trace.rule_hits_by_type).length : 0;
  const truncationCount = result ? result.analysis_trace.patch_truncated_file_count : 0;

  const handleAnalyze = async () => {
    if (!prUrl.trim()) {
      setError("Please enter a GitHub PR URL first.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await analyzePullRequest({
        pr_url: prUrl.trim(),
        github_token: githubToken,
        use_ai: useAi,
      });
      setResult(response);
      setResultSequence((current) => current + 1);
    } catch (requestError) {
      if (requestError instanceof Error) {
        setError(requestError.message);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setIsResetting(true);
    setPrUrl("");
    setGithubToken("");
    setUseAi(false);
    setError("");
    setResult(null);
    window.setTimeout(() => setIsResetting(false), 280);
  };

  return (
    <div className="app-shell">
      <div className="app-backdrop" aria-hidden="true">
        <div className="backdrop-orb backdrop-orb-one" />
        <div className="backdrop-orb backdrop-orb-two" />
        <div className="backdrop-grid" />
      </div>

      <div className="app-grid">
        <aside className="control-rail">
          <section className="control-card hero-panel motion-enter motion-delay-0">
            <div className="eyebrow">AI Code Review Console</div>
            <h1>CodeLens</h1>
            <p className="hero-copy">
              A developer-first PR review console that brings GitHub diff context,
              rule-based risk detection, and AI review into one live workspace.
            </p>

            <div className="hero-metrics">
              <div className="metric-chip">
                <span className="metric-label">Pipeline</span>
                <strong>GitHub → Diff → Risk → AI</strong>
              </div>
              <div className="metric-chip">
                <span className="metric-label">Output</span>
                <strong>Markdown Review Report</strong>
              </div>
            </div>

            <div className="feature-list">
              <div className="feature-item">
                <span className="feature-dot" />
                Pull PR metadata and change summaries automatically
              </div>
              <div className="feature-item">
                <span className="feature-dot" />
                Detect high-confidence risks with explicit severity
              </div>
              <div className="feature-item">
                <span className="feature-dot" />
                Export a copy-ready Markdown review report
              </div>
            </div>
          </section>

          <ReviewForm
            prUrl={prUrl}
            githubToken={githubToken}
            useAi={useAi}
            loading={loading}
            isResetting={isResetting}
            onPrUrlChange={setPrUrl}
            onTokenChange={setGithubToken}
            onUseAiChange={setUseAi}
            onSubmit={handleAnalyze}
            onReset={handleReset}
          />

          <section className="control-card system-card motion-enter motion-delay-2">
            <div className="card-caption">System Status</div>
            <div className="status-row">
              <span>Review Engine</span>
              <strong>{loading ? "Running" : hasResult ? "Ready" : "Idle"}</strong>
            </div>
            <div className="status-row">
              <span>AI Review</span>
              <strong>{useAi ? "Enabled" : "Disabled"}</strong>
            </div>
            <div className="status-row">
              <span>Token Mode</span>
              <strong>{githubToken.trim() ? "Authenticated" : "Public API"}</strong>
            </div>
            <div className="status-row">
              <span>Workspace</span>
              <strong>Local Demo</strong>
            </div>
          </section>
        </aside>

        <main className="workspace">
          <section className="workspace-header motion-enter motion-delay-1">
            <div>
              <div className="eyebrow">Review Workspace</div>
              <h2>Pull Request Intelligence Board</h2>
            </div>
            <div className="workspace-badges">
              <span className="badge badge-outline">Rule + AI Hybrid</span>
              <span className="badge badge-outline">GitHub Native Context</span>
              <span className="badge badge-outline">Demo Ready</span>
            </div>
          </section>

          {error ? <ErrorBanner message={error} /> : null}
          {loading ? <LoadingState /> : null}

          {!loading && !hasResult ? (
            <section className="card empty-hangar motion-enter motion-delay-3">
              <div className="empty-radar" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <div className="empty-copy">
                <h3>Waiting for a Pull Request</h3>
                <p>
                  Paste a GitHub PR URL on the left and CodeLens will fetch context,
                  parse the diff, scan for risks, and prepare an AI-assisted review.
                </p>
              </div>
            </section>
          ) : null}

          {!loading && result ? (
            <div key={resultSequence} className="result-stack">
              <section className="card hero-report reveal-panel reveal-delay-0">
                <div className="hero-report-main">
                  <div className="card-caption">Mission Summary</div>
                  <h3>{result.pr.title}</h3>
                  <p>{result.summary}</p>
                </div>
                <div className="hero-report-side">
                  <span className="signal-pill">Mode: {formatReviewMode(result.review_mode)}</span>
                  <span className="signal-pill">AI: {getAiStatusLabel(result.analysis_trace.ai_status)}</span>
                  <span className="signal-pill">Rule Types: {ruleTypeCount}</span>
                  <span className="signal-pill">Files: {result.stats.file_count}</span>
                </div>
              </section>

              {truncationCount > 0 ? (
                <section className="warning-panel reveal-panel reveal-delay-1">
                  <div className="warning-icon">!</div>
                  <div>
                    <strong>Patch truncation detected</strong>
                    <p>
                      GitHub truncated patch content for {truncationCount} file(s).
                      Review the original PR page for a deeper manual check.
                    </p>
                  </div>
                </section>
              ) : null}

              <section className="card stat-deck reveal-panel reveal-delay-2">
                <div className="stat-tile stat-tile-highlight">
                  <span className="metric-label">Changed Files</span>
                  <strong>{result.stats.file_count}</strong>
                </div>
                <div className="stat-tile">
                  <span className="metric-label">Additions</span>
                  <strong>+{result.stats.total_additions}</strong>
                </div>
                <div className="stat-tile">
                  <span className="metric-label">Deletions</span>
                  <strong>-{result.stats.total_deletions}</strong>
                </div>
                <div
                  className={
                    result.risk_summary.high > 0
                      ? "stat-tile stat-tile-danger"
                      : "stat-tile"
                  }
                >
                  <span className="metric-label">Risk Count</span>
                  <strong>{result.risk_summary.total}</strong>
                </div>
              </section>

              <div className="workspace-grid workspace-grid-top">
                <PrInfoCard className="reveal-panel reveal-delay-3" pr={result.pr} />
                <RiskSummaryCard className="reveal-panel reveal-delay-4" riskSummary={result.risk_summary} />
              </div>

              <AnalysisTraceCard
                className="reveal-panel reveal-delay-5"
                analysisTrace={result.analysis_trace}
              />
              <RiskTable className="reveal-panel reveal-delay-6" risks={result.risks} />

              <div className="workspace-grid workspace-grid-bottom">
                <AiReviewPanel
                  className="reveal-panel reveal-delay-7"
                  aiReview={result.ai_review}
                  reviewMode={result.review_mode}
                />
                <MarkdownReport
                  className="reveal-panel reveal-delay-8"
                  markdown_report={result.markdown_report}
                  markdownReport={result.markdownReport}
                />
              </div>
            </div>
          ) : null}
        </main>
      </div>
    </div>
  );
}
