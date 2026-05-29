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
    <section className="card">
      <h2>Review 输入</h2>
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
          GitHub Token（推荐填写，用于避免 GitHub API 限流）
          <input
            type="password"
            value={githubToken}
            onChange={(event) => onTokenChange(event.target.value)}
            placeholder="ghp_... 或 github_pat_...，仅本次请求使用"
            autoComplete="off"
            disabled={loading}
          />
        </label>
        {!githubToken.trim() ? (
          <p className="token-hint">未填写 Token 时只能访问公开仓库，且可能触发 GitHub API rate limit。</p>
        ) : null}

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={useAi}
            onChange={(event) => onUseAiChange(event.target.checked)}
            disabled={loading}
          />
          启用 AI Review
        </label>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "分析中..." : "开始分析"}
          </button>
          <button type="button" className="btn" onClick={onReset} disabled={loading}>
            清空
          </button>
        </div>
      </form>

      <p className="security-note">
        Token 仅用于本次请求，不会保存到浏览器存储，也不会写入项目文件。
      </p>
    </section>
  );
}
