import { FormEvent } from "react";

interface ReviewFormProps {
  prUrl: string;
  githubToken: string;
  useAi: boolean;
  loading: boolean;
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

  return (
    <section className="control-card review-console">
      <div className="card-caption">Input Console</div>
      <h2>Launch Review</h2>

      <form className="review-form" onSubmit={handleSubmit}>
        <label>
          GitHub PR URL <span className="required">*</span>
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
          GitHub Token
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
            ? "已开启鉴权请求，能更稳定地读取 GitHub PR 变更。"
            : "未填写 Token 时只能访问公开仓库，且更容易触发 GitHub API 限流。"}
        </div>

        <label className="toggle-row">
          <div>
            <span className="toggle-title">AI Review</span>
            <p className="toggle-copy">启用后会在规则分析之外生成 PR 总结、风险判断和修改建议。</p>
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
            {loading ? "Review Running..." : "Start Analysis"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={onReset} disabled={loading}>
            Reset Console
          </button>
        </div>
      </form>

      <p className="security-note">
        Token 仅用于本次请求，不会写入 localStorage、sessionStorage、cookie 或项目文件。
      </p>
    </section>
  );
}
