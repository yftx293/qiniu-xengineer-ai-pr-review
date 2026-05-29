export interface ReviewRequest {
  pr_url: string;
  github_token: string;
  use_ai: boolean;
}

export interface ParsedSource {
  owner: string;
  repo: string;
  pull_number: number;
  api_url: string;
  html_url: string;
}

export interface PullRequestInfo {
  title: string;
  number: number;
  state: string;
  author: string;
  html_url: string;
  base_branch: string;
  head_branch: string;
  created_at: string;
  updated_at: string;
  additions: number;
  deletions: number;
  changed_files: number;
}

export interface ChangedFile {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  raw_url: string;
  blob_url: string;
  patch: string;
  patch_truncated: boolean;
}

export interface PullRequestStats {
  file_count: number;
  total_additions: number;
  total_deletions: number;
  total_changes: number;
}

export interface RiskItem {
  file: string | null;
  line: number | null;
  severity: "High" | "Medium" | "Low" | string;
  type: string;
  message: string;
  evidence: string | null;
  suggestion: string;
  confidence: "High" | "Medium" | "Low" | string;
}

export interface RiskSummary {
  total: number;
  high: number;
  medium: number;
  low: number;
  has_blocking_risk: boolean;
}

export interface AIReviewResult {
  enabled: boolean;
  error: string | null;
  pr_summary: string;
  main_changes: string[];
  risk_analysis: string[];
  review_suggestions: string[];
  overall_risk_level: "High" | "Medium" | "Low" | string;
  confidence: "High" | "Medium" | "Low" | string;
}

export interface AnalysisTrace {
  rule_hits_by_type: Record<string, number>;
  patch_truncated_file_count: number;
  context_source: string;
  ai_status: string;
}

export interface ReviewResponse {
  message: string;
  source: ParsedSource;
  pr: PullRequestInfo;
  files: ChangedFile[];
  stats: PullRequestStats;
  summary: string;
  risks: RiskItem[];
  suggestions: string[];
  risk_summary: RiskSummary;
  ai_review: AIReviewResult | null;
  analysis_trace: AnalysisTrace;
  markdown_report: string;
  markdownReport?: string;
  review_mode: "rule_based" | "ai_assisted" | "ai_fallback" | string;
  use_ai: boolean;
}
