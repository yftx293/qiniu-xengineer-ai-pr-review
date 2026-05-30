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
    ? "control-card review-console motion-enter motion-delay-1 is-resetting"
    : "control-card review-console motion-enter motion-delay-1";

  return (
    <section className={panelClassName}>
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
            ? "Authenticated requests are enabled for more reliable GitHub PR access."
            : "Without a token, only public repositories are available and rate limits are easier to hit."}
        </div>

        <label className="toggle-row">
          <div>
            <span className="toggle-title">AI Review</span>
            <p className="toggle-copy">
              Add PR summaries, risk reasoning, and actionable review suggestions on top of rule analysis.
            </p>
            <span className={useAi ? "toggle-state is-on" : "toggle-state"}>
              {useAi ? "AI enhancement enabled" : "Rule-only review mode"}
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
            {loading ? "Review Running..." : "Start Analysis"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={onReset} disabled={loading}>
            Reset Console
          </button>
        </div>
      </form>

      <p className="security-note">
        Tokens are used only for this request and are never written to local storage, session storage, cookies, or project files.
      </p>
    </section>
  );
}
