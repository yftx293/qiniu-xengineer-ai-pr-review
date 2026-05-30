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
import DualEngineCard from "./components/DualEngineCard";

function getModeBadge(result: ReviewResponse): string {
  switch (result.review_mode) {
    case "ai_assisted":
      return "AI Assisted";
    case "ai_fallback":
      return "Rules + Fallback";
    case "rule_based":
      return "Rules Only";
    default:
      return result.review_mode;
  }
}

function getContextBadge(result: ReviewResponse): string {
  return result.analysis_trace.patch_truncated_file_count > 0 ? "Partial Context" : "Full Context";
}

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
        <p className="eyebrow">CodeLens AI PR Review Assistant</p>
        <h1>从 GitHub PR 链接到结构化代码审查结果</h1>
        <p>
          输入一个 GitHub PR URL，系统会自动抓取 diff、扫描高确定性风险，并生成 reviewer 风格的结构化 Review 建议。
        </p>
      </header>

      <section className="hero-grid">
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

        <section className="card capability-card">
          <p className="eyebrow">Why it stands out</p>
          <h2>Dual Engine Review, not a plain chatbot</h2>
          <div className="capability-list">
            <article>
              <h3>Rule Scan</h3>
              <p>识别硬编码密钥、危险函数、SQL 注入、测试缺失、权限敏感改动等高确定性风险。</p>
            </article>
            <article>
              <h3>AI Reviewer</h3>
              <p>基于关键文件上下文生成更像资深 reviewer 的总结、风险判断和建议，而不是泛泛而谈。</p>
            </article>
            <article>
              <h3>Markdown Output</h3>
              <p>输出可复制的 Markdown Review 报告，适合贴回 PR、答辩展示或团队内部复盘。</p>
            </article>
          </div>
        </section>
      </section>

      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <LoadingState /> : null}

      {!loading && !hasResult ? (
        <section className="card empty-state">
          输入一个公开可访问的 GitHub PR 链接，即可开始一次从 diff 到结构化 review 的完整分析。
        </section>
      ) : null}

      {!loading && result ? (
        <>
          <section className="card result-hero">
            <div className="hero-copy">
              <p className="eyebrow">Review Conclusion</p>
              <h3>这次分析给出的第一结论</h3>
              <p>{result.message}</p>
              <p className="muted hero-summary">{result.summary}</p>
            </div>
            <div className="hero-badges">
              <span className="badge badge-contrast">{getModeBadge(result)}</span>
              <span className="badge">Rules + LLM</span>
              <span className="badge">{getContextBadge(result)}</span>
              <span className="badge">AI Status: {result.analysis_trace.ai_status}</span>
            </div>
          </section>

          {result.analysis_trace.patch_truncated_file_count > 0 ? (
            <section className="card warning-card">
              <h3>上下文截断提示</h3>
              <p>
                本次分析中有 {result.analysis_trace.patch_truncated_file_count} 个文件的 patch 内容被截断。
                当前结果仍适合做快速 Review，但对于超大 PR，建议回到 GitHub 原始 Diff 再做一次人工确认。
              </p>
            </section>
          ) : null}

          <div className="grid-two">
            <PrInfoCard pr={result.pr} />

            <section className="card">
              <p className="eyebrow">Core Metrics</p>
              <h3>PR 核心统计</h3>
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

          <div className="grid-two">
            <RiskSummaryCard riskSummary={result.risk_summary} />
            <AnalysisTraceCard analysisTrace={result.analysis_trace} />
          </div>

          <DualEngineCard
            aiReview={result.ai_review}
            analysisTrace={result.analysis_trace}
            riskSummary={result.risk_summary}
            reviewMode={result.review_mode}
          />

          <RiskTable risks={result.risks} />
          <AiReviewPanel
            aiReview={result.ai_review}
            analysisTrace={result.analysis_trace}
            reviewMode={result.review_mode}
          />
          <MarkdownReport
            markdown_report={result.markdown_report}
            markdownReport={result.markdownReport}
          />
        </>
      ) : null}
    </div>
  );
}
