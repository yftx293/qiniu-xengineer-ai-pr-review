const loadingPhases = [
  "获取 PR 元信息",
  "解析 changed files",
  "扫描规则风险",
  "准备 reviewer 总结",
];

export default function LoadingState() {
  return (
    <section className="card loading-card motion-enter motion-delay-2" aria-live="polite">
      <div className="loading-scan-line" />
      <div className="loading-wrap">
        <div className="spinner" />
        <div>
          <h3>正在分析这次 PR</h3>
          <p className="muted">CodeLens 正在从 GitHub 上下文、规则扫描和 AI 辅助中构建这次结构化审查结果。</p>
        </div>
      </div>

      <div className="loading-phase-grid">
        {loadingPhases.map((phase) => (
          <div key={phase} className="loading-phase">
            <span className="loading-dot" />
            <span>{phase}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
