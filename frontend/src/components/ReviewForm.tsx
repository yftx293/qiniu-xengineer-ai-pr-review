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
          GitHub Token（可选）
          <input
            type="password"
            value={githubToken}
            onChange={(event) => onTokenChange(event.target.value)}
            placeholder="可留空，公开仓库一般可直接访问"
            autoComplete="off"
            disabled={loading}
          />
        </label>

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
        GitHub Token 仅用于本次请求，不会在前端保存，也不会写入项目文件。
      </p>
    </section>
  );
}
