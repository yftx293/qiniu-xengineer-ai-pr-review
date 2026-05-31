import { FormEvent } from "react";

interface ReviewFormProps {
  prUrl: string;
  githubToken: string;
  useAi: boolean;
  loading: boolean;
  isResetting: boolean;
  onPrUrlChange: (value: string) => void;
  onTokenChange: (value: string) => void;
  onUseAiChange: (value: boolean) => void;
  onSubmit: () => void;
  onReset: () => void;
}

export default function ReviewForm(props: ReviewFormProps) {
  const {
    prUrl,
    githubToken,
    useAi,
    loading,
    isResetting,
    onPrUrlChange,
    onTokenChange,
    onUseAiChange,
    onSubmit,
    onReset,
  } = props;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    onSubmit();
  };

  const panelClassName = isResetting
    ? "card control-card review-console motion-enter motion-delay-1 is-resetting"
    : "card control-card review-console motion-enter motion-delay-1";

  return (
    <section className={panelClassName}>
      <div className="card-caption">Launch Review Console</div>
      <h2>从一个 PR 链接开始这次审查</h2>
      <p className="muted panel-intro">
        贴入 GitHub Pull Request 链接后，系统会自动抓取变更、扫描规则风险，并在需要时叠加 AI Reviewer
        的总结和建议。
      </p>

      <form className="review-form" onSubmit={handleSubmit}>
        <label>
          GitHub PR 链接 <span className="required">*</span>
          <input
            type="url"
            value={prUrl}
            onChange={(event) => onPrUrlChange(event.target.value)}
            placeholder="https://github.com/owner/repo/pull/123"
            required
            disabled={loading}
          />
        </label>

        <label>
          GitHub Token（可选）
          <input
            type="password"
            value={githubToken}
            onChange={(event) => onTokenChange(event.target.value)}
            placeholder="ghp_... or github_pat_..."
            autoComplete="off"
            disabled={loading}
          />
        </label>

        <div className="helper-panel">
          {githubToken.trim()
            ? "当前将使用认证请求，访问公开仓库会更稳定，也更不容易触发 GitHub API rate limit。"
            : "未填写 Token 时，只适合公开仓库，且更容易触发 GitHub API rate limit。"}
        </div>

        <label className="toggle-row">
          <div>
            <span className="toggle-title">启用 AI Review</span>
            <p className="toggle-copy">在规则分析基础上，补充 PR 总结、风险解释和更像 reviewer 的修改建议。</p>
            <span className={useAi ? "toggle-state is-on" : "toggle-state"}>
              {useAi ? "AI 辅助已开启" : "当前为规则优先模式"}
            </span>
          </div>
          <input
            type="checkbox"
            checked={useAi}
            onChange={(event) => onUseAiChange(event.target.checked)}
            disabled={loading}
          />
        </label>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "正在分析..." : "开始分析"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={onReset} disabled={loading}>
            重置控制台
          </button>
        </div>
      </form>

      <div className="review-console-footnote">
        <span>规则引擎</span>
        <span>AI Reviewer</span>
        <span>Markdown 报告</span>
      </div>

      <p className="security-note">
        Token 仅用于本次请求，不会被写入 localStorage、sessionStorage、cookie 或项目文件。
      </p>
    </section>
  );
}
