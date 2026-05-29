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

export default function App() {
  const [prUrl, setPrUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ReviewResponse | null>(null);

  const hasResult = useMemo(() => result !== null, [result]);
  const ruleTypeCount = result ? Object.keys(result.analysis_trace.rule_hits_by_type).length : 0;
  const truncationCount = result ? result.analysis_trace.patch_truncated_file_count : 0;

  const handleAnalyze = async () => {
    if (!prUrl.trim()) {
      setError("请先输入 GitHub PR URL。");
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
    } catch (requestError) {
      if (requestError instanceof Error) {
        setError(requestError.message);
      } else {
        setError("发生未知错误，请稍后重试。");
      }
      setResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPrUrl("");
    setGithubToken("");
    setUseAi(false);
    setError("");
    setResult(null);
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
          <section className="control-card hero-panel">
            <div className="eyebrow">AI Code Review Console</div>
            <h1>CodeLens</h1>
            <p className="hero-copy">
              面向开发者的 PR 审查工作台，把 GitHub Diff、规则检测和 AI Review
              汇聚到同一块控制面板里。
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
                自动抓取 PR 元数据与变更摘要
              </div>
              <div className="feature-item">
                <span className="feature-dot" />
                规则识别高确定性风险并标记等级
              </div>
              <div className="feature-item">
                <span className="feature-dot" />
                生成可直接复制的 Markdown Review 报告
              </div>
            </div>
          </section>

          <ReviewForm
            prUrl={prUrl}
            githubToken={githubToken}
            useAi={useAi}
            loading={loading}
            onPrUrlChange={setPrUrl}
            onTokenChange={setGithubToken}
            onUseAiChange={setUseAi}
            onSubmit={handleAnalyze}
            onReset={handleReset}
          />

          <section className="control-card system-card">
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
          <section className="workspace-header">
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
            <section className="card empty-hangar">
              <div className="empty-radar" aria-hidden="true">
                <span />
                <span />
                <span />
              </div>
              <div className="empty-copy">
                <h3>等待接入一个 Pull Request</h3>
                <p>
                  在左侧输入 GitHub PR 链接后，系统会依次完成上下文抓取、Diff 解析、规则审查和
                  AI Review 生成。
                </p>
              </div>
            </section>
          ) : null}

          {!loading && result ? (
            <>
              <section className="card hero-report">
                <div className="hero-report-main">
                  <div className="card-caption">Mission Summary</div>
                  <h3>{result.pr.title}</h3>
                  <p>{result.summary}</p>
                </div>
                <div className="hero-report-side">
                  <span className="signal-pill">Mode: {formatReviewMode(result.review_mode)}</span>
                  <span className="signal-pill">AI: {result.analysis_trace.ai_status}</span>
                  <span className="signal-pill">Rule Types: {ruleTypeCount}</span>
                  <span className="signal-pill">Files: {result.stats.file_count}</span>
                </div>
              </section>

              {truncationCount > 0 ? (
                <section className="warning-panel">
                  <div className="warning-icon">!</div>
                  <div>
                    <strong>检测到上下文截断</strong>
                    <p>
                      当前有 {truncationCount} 个文件的 patch 内容被 GitHub 截断，建议结合原始 PR
                      页面进一步复核。
                    </p>
                  </div>
                </section>
              ) : null}

              <section className="card stat-deck">
                <div className="stat-tile">
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
                <div className="stat-tile">
                  <span className="metric-label">Risk Count</span>
                  <strong>{result.risk_summary.total}</strong>
                </div>
              </section>

              <div className="workspace-grid workspace-grid-top">
                <PrInfoCard pr={result.pr} />
                <RiskSummaryCard riskSummary={result.risk_summary} />
              </div>

              <AnalysisTraceCard analysisTrace={result.analysis_trace} />
              <RiskTable risks={result.risks} />

              <div className="workspace-grid workspace-grid-bottom">
                <AiReviewPanel aiReview={result.ai_review} reviewMode={result.review_mode} />
                <MarkdownReport
                  markdown_report={result.markdown_report}
                  markdownReport={result.markdownReport}
                />
              </div>
            </>
          ) : null}
        </main>
      </div>
    </div>
  );
}
