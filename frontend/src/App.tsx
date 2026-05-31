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

function getAiStatusLabel(result: ReviewResponse): string {
  switch (result.analysis_trace.ai_status) {
    case "completed":
      return "AI 已参与";
    case "config_missing":
      return "未配置 AI";
    case "fallback_error":
      return "AI 已回退";
    default:
      return "规则优先";
  }
}

export default function App() {
  const [prUrl, setPrUrl] = useState("");
  const [githubToken, setGithubToken] = useState("");
  const [useAi, setUseAi] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [isResetting, setIsResetting] = useState(false);

  const hasResult = useMemo(() => result !== null, [result]);

  const heroMetrics = useMemo(() => {
    if (!result) {
      return [
        { label: "审查模式", value: "规则 + AI 协同" },
        { label: "输出结果", value: "结构化 Review" },
        { label: "定位方式", value: "风险 + 解释 + 报告" },
        { label: "适用场景", value: "PR 快速复核" },
      ];
    }

    return [
      { label: "变更文件", value: `${result.stats.file_count}` },
      { label: "风险总数", value: `${result.risk_summary.total}` },
      { label: "高风险项", value: `${result.risk_summary.high}` },
      { label: "AI 参考文件", value: `${result.analysis_trace.ai_context_file_count ?? 0}` },
    ];
  }, [result]);

  const handleAnalyze = async () => {
    if (!prUrl.trim()) {
      setError("请先输入 GitHub PR 链接。");
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
    setIsResetting(true);
    setPrUrl("");
    setGithubToken("");
    setUseAi(false);
    setError("");
    setResult(null);
    window.setTimeout(() => setIsResetting(false), 320);
  };

  return (
    <div className="app-shell">
      <header className="page-header">
        <div className="header-intro">
          <div className="headline-block">
            <p className="eyebrow">Precision Review Console</p>
            <h1>输入 GitHub PR 链接，快速得到结构化代码审查结论</h1>
            <p className="header-copy">
              CodeLens 会自动抓取 PR diff、扫描高确定性风险，并结合 AI Reviewer 生成更像资深工程师的总结、
              风险解释与可复制的 Markdown Review 报告。
            </p>
          </div>

          <div className="header-rail">
            {heroMetrics.map((item) => (
              <article key={item.label} className="signal-card">
                <span>{item.label}</span>
                <strong>{item.value}</strong>
              </article>
            ))}
          </div>
        </div>
      </header>

      <section className="hero-grid">
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

        <section className="card capability-card motion-enter motion-delay-2">
          <div className="card-caption">Review Blueprint</div>
          <h2>不是简单问答，而是一条完整的 PR 审查闭环</h2>

          <div className="capability-list">
            <article>
              <h3>规则引擎扫描</h3>
              <p>优先识别密钥泄露、危险执行入口、SQL 拼接、测试缺失和权限敏感改动等高确定性风险。</p>
            </article>
            <article>
              <h3>AI Reviewer 理解</h3>
              <p>聚焦关键 diff 和高风险文件，生成更像资深 reviewer 的影响判断、风险解释和修改建议。</p>
            </article>
            <article>
              <h3>结构化交付</h3>
              <p>页面展示 + 风险表格 + Markdown 报告同步输出，适合 PR 复核、答辩演示和团队复盘。</p>
            </article>
          </div>

          <div className="telemetry-strip">
            <span>Rule Engine</span>
            <span>AI Reviewer</span>
            <span>Markdown Report</span>
          </div>
        </section>
      </section>

      {error ? <ErrorBanner message={error} /> : null}
      {loading ? <LoadingState /> : null}

      {!loading && !hasResult ? (
        <section className="card empty-state motion-enter motion-delay-3">
          <div className="empty-radar" aria-hidden="true" />
          <h3>等待一次新的 PR 审查任务</h3>
          <p>
            输入一个公开可访问的 GitHub PR 链接，系统会完成 PR 获取、diff 解析、规则扫描和可选 AI 审查，
            最终生成适合直接阅读与复制的结构化结果。
          </p>
        </section>
      ) : null}

      {!loading && result ? (
        <>
          <section className="card result-hero motion-enter motion-delay-1">
            <div className="hero-copy">
              <p className="eyebrow">Review Conclusion</p>
              <h3>第一结论先给你，剩下的细节再往下看</h3>
              <p className="hero-message">{result.message}</p>
              <p className="muted hero-summary">{result.summary}</p>
            </div>
            <div className="hero-badges">
              <span className="badge badge-contrast">{getModeBadge(result)}</span>
              <span className="badge">{getContextBadge(result)}</span>
              <span className="badge">{getAiStatusLabel(result)}</span>
              <span className="badge">风险 {result.risk_summary.total} 项</span>
            </div>
          </section>

          {result.analysis_trace.patch_truncated_file_count > 0 ? (
            <section className="card warning-card motion-enter motion-delay-2">
              <h3>上下文截断提示</h3>
              <p>
                本次分析中有 {result.analysis_trace.patch_truncated_file_count} 个文件的 patch 内容被截断。当前结果仍适合做快速
                Review，但对于超大 PR，建议回到 GitHub 原始 Diff 再做一次人工确认。
              </p>
            </section>
          ) : null}

          <section className="dashboard-grid">
            <PrInfoCard pr={result.pr} className="motion-enter motion-delay-2" />

            <section className="card surface-card motion-enter motion-delay-3">
              <div className="card-caption">Core Metrics</div>
              <h3>本次审查的核心统计</h3>
              <div className="summary-grid summary-grid-compact">
                <div className="summary-tile">
                  <span>变更文件</span>
                  <strong>{result.stats.file_count}</strong>
                </div>
                <div className="summary-tile">
                  <span>新增行数</span>
                  <strong>+{result.stats.total_additions}</strong>
                </div>
                <div className="summary-tile">
                  <span>删除行数</span>
                  <strong>-{result.stats.total_deletions}</strong>
                </div>
                <div className="summary-tile">
                  <span>总改动</span>
                  <strong>{result.stats.total_changes}</strong>
                </div>
              </div>
            </section>

            <RiskSummaryCard riskSummary={result.risk_summary} className="motion-enter motion-delay-4" />
          </section>

          <section className="grid-two">
            <AnalysisTraceCard analysisTrace={result.analysis_trace} />
            <DualEngineCard
              aiReview={result.ai_review}
              analysisTrace={result.analysis_trace}
              riskSummary={result.risk_summary}
              reviewMode={result.review_mode}
            />
          </section>

          <RiskTable risks={result.risks} />

          <AiReviewPanel
            aiReview={result.ai_review}
            analysisTrace={result.analysis_trace}
            reviewMode={result.review_mode}
          />

          <MarkdownReport markdown_report={result.markdown_report} markdownReport={result.markdownReport} />
        </>
      ) : null}
    </div>
  );
}
