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

export default function App() {
  const [prUrl, setPrUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ReviewResponse | null>(null);

  const hasResult = useMemo(() => result !== null, [result]);

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
      <header className="page-header">
        <h1>CodeLens AI PR Review Assistant</h1>
        <p>输入 GitHub PR 链接，自动生成变更总结、风险识别和 Review 建议。</p>
      </header>

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

      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <LoadingState /> : null}

      {!loading && !hasResult ? (
        <section className="card empty-state">请先输入一个 GitHub PR 链接并开始分析。</section>
      ) : null}

      {!loading && result ? (
        <>
          <section className="card">
            <h3>分析结论</h3>
            <p>{result.message}</p>
            <p className="muted">{result.summary}</p>
          </section>

          <div className="grid-two">
            <PrInfoCard pr={result.pr} />

            <section className="card">
              <h3>变更统计</h3>
              <div className="kv-grid">
                <div>
                  <span className="k">File Count</span>
                  <span className="v">{result.stats.file_count}</span>
                </div>
                <div>
                  <span className="k">Total Additions</span>
                  <span className="v">+{result.stats.total_additions}</span>
                </div>
                <div>
                  <span className="k">Total Deletions</span>
                  <span className="v">-{result.stats.total_deletions}</span>
                </div>
                <div>
                  <span className="k">Total Changes</span>
                  <span className="v">{result.stats.total_changes}</span>
                </div>
              </div>
            </section>
          </div>

          <RiskSummaryCard riskSummary={result.risk_summary} />
          <RiskTable risks={result.risks} />
          <AiReviewPanel aiReview={result.ai_review} reviewMode={result.review_mode} />
          <MarkdownReport
            markdown_report={result.markdown_report}
            markdownReport={result.markdownReport}
          />
        </>
      ) : null}
    </div>
  );
}
