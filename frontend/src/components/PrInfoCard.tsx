import type { PullRequestInfo } from "../types";

interface PrInfoCardProps {
  pr: PullRequestInfo;
}

export default function PrInfoCard({ pr }: PrInfoCardProps) {
  return (
    <section className="card">
      <h3>PR 基本信息</h3>
      <div className="kv-grid">
        <div>
          <span className="k">标题</span>
          <span className="v">{pr.title}</span>
        </div>
        <div>
          <span className="k">作者</span>
          <span className="v">{pr.author}</span>
        </div>
        <div>
          <span className="k">状态</span>
          <span className="v">{pr.state}</span>
        </div>
        <div>
          <span className="k">分支</span>
          <span className="v">{pr.head_branch} → {pr.base_branch}</span>
        </div>
        <div>
          <span className="k">变更文件数</span>
          <span className="v">{pr.changed_files}</span>
        </div>
        <div>
          <span className="k">Additions / Deletions</span>
          <span className="v">+{pr.additions} / -{pr.deletions}</span>
        </div>
      </div>
      <a href={pr.html_url} target="_blank" rel="noreferrer" className="link">
        查看 GitHub PR
      </a>
    </section>
  );
}
