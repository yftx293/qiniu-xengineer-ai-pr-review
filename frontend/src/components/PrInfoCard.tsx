import type { PullRequestInfo } from "../types";

interface PrInfoCardProps {
  pr: PullRequestInfo;
  className?: string;
}

function formatDate(value: string): string {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function PrInfoCard({ pr, className = "" }: PrInfoCardProps) {
  const sectionClassName = className ? `card surface-card ${className}` : "card surface-card";

  return (
    <section className={sectionClassName}>
      <div className="card-topline">
        <div className="card-caption">Pull Request</div>
        <span className={`state-pill state-${pr.state.toLowerCase()}`}>{pr.state}</span>
      </div>

      <h3>PR Overview</h3>

      <div className="kv-grid">
        <div>
          <span className="k">Title</span>
          <span className="v">{pr.title}</span>
        </div>
        <div>
          <span className="k">Author</span>
          <span className="v">{pr.author}</span>
        </div>
        <div>
          <span className="k">Branch Flow</span>
          <span className="v">
            {pr.head_branch} → {pr.base_branch}
          </span>
        </div>
        <div>
          <span className="k">Changed Files</span>
          <span className="v">{pr.changed_files}</span>
        </div>
        <div>
          <span className="k">Created At</span>
          <span className="v">{formatDate(pr.created_at)}</span>
        </div>
        <div>
          <span className="k">Updated At</span>
          <span className="v">{formatDate(pr.updated_at)}</span>
        </div>
        <div>
          <span className="k">Code Delta</span>
          <span className="v">
            +{pr.additions} / -{pr.deletions}
          </span>
        </div>
      </div>

      <a href={pr.html_url} target="_blank" rel="noreferrer" className="link">
        Open on GitHub
      </a>
    </section>
  );
}
