import { useState } from "react";

interface MarkdownReportProps {
  report: string;
}

export default function MarkdownReport({ report }: MarkdownReportProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(report);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch {
      setCopied(false);
    }
  };

  return (
    <section className="card">
      <div className="card-head-row">
        <h3>Markdown 报告</h3>
        <button type="button" className="btn btn-primary" onClick={handleCopy}>
          {copied ? "已复制" : "复制 Markdown 报告"}
        </button>
      </div>
      <pre className="markdown-box">{report}</pre>
    </section>
  );
}
