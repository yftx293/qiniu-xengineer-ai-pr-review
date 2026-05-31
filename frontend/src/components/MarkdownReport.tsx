import { useRef, useState } from "react";

interface MarkdownReportProps {
  markdown_report?: string;
  markdownReport?: string;
  className?: string;
}

export default function MarkdownReport({
  markdown_report,
  markdownReport,
  className = "",
}: MarkdownReportProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");

  const markdown = (markdown_report ?? markdownReport ?? "").trim();
  const sectionClassName = className ? `card surface-card ${className}` : "card surface-card";

  const setCopiedState = () => {
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  const fallbackCopy = (content: string): boolean => {
    const tempTextarea = document.createElement("textarea");
    tempTextarea.value = content;
    tempTextarea.setAttribute("readonly", "true");
    tempTextarea.style.position = "fixed";
    tempTextarea.style.left = "-9999px";
    tempTextarea.style.top = "0";

    document.body.appendChild(tempTextarea);
    tempTextarea.focus();
    tempTextarea.select();

    let success = false;
    try {
      success = document.execCommand("copy");
    } catch {
      success = false;
    }

    document.body.removeChild(tempTextarea);
    return success;
  };

  const handleCopy = async () => {
    if (!markdown) {
      setCopyError("暂无 Markdown 报告");
      return;
    }

    setCopyError("");

    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(markdown);
        setCopiedState();
        return;
      } catch {
        // Fallback below.
      }
    }

    const success = fallbackCopy(markdown);
    if (success) {
      setCopiedState();
      return;
    }

    setCopyError("自动复制失败，请手动选择下方报告内容复制。");
  };

  const handleSelectAll = () => {
    if (!textareaRef.current) {
      return;
    }
    textareaRef.current.focus();
    textareaRef.current.select();
  };

  return (
    <section className={sectionClassName}>
      <div className="card-head-row">
        <div>
          <p className="eyebrow">Export</p>
          <h3>可复制的 Markdown 审查报告</h3>
        </div>
        <div className="card-actions">
          <button type="button" className="btn" onClick={handleSelectAll}>
            全选
          </button>
          <button type="button" className="btn btn-primary" onClick={handleCopy}>
            {copied ? "已复制" : "复制 Markdown 报告"}
          </button>
        </div>
      </div>
      {copyError ? <p className="error-inline">{copyError}</p> : null}
      <textarea
        ref={textareaRef}
        className="markdown-textarea"
        readOnly
        value={markdown || "暂无 Markdown 报告"}
      />
    </section>
  );
}
