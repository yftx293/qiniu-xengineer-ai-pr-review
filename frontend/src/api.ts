import type { ReviewRequest, ReviewResponse } from "./types";

const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 120000;

function getApiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/$/, "");
}

function extractErrorDetail(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "";
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (detail && typeof detail === "object" && "message" in detail) {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") {
      return message;
    }
  }

  return "";
}

function sanitizeDetail(detail: string): string {
  return detail.replace(/\s+/g, " ").trim().slice(0, 180);
}

function mapBackendError(status: number, detail: string): string {
  const normalized = detail.toLowerCase();
  const safeDetail = sanitizeDetail(detail);

  if (normalized.includes("rate limit") || normalized.includes("please provide github_token")) {
    return safeDetail
      ? `GitHub API 访问频率受限，请填写 GitHub Token 后重试。后端信息：${safeDetail}`
      : "GitHub API 访问频率受限，请填写 GitHub Token 后重试。";
  }

  if (status === 401 || status === 403) {
    return safeDetail
      ? `GitHub Token 无效、权限不足或访问频率受限，请检查 Token 后重试。后端信息：${safeDetail}`
      : "GitHub Token 无效、权限不足或访问频率受限，请检查 Token 后重试。";
  }

  if (status === 404) {
    return safeDetail
      ? `未找到该 PR，请确认仓库、PR 编号或 Token 权限。后端信息：${safeDetail}`
      : "未找到该 PR，请确认仓库、PR 编号或 Token 权限。";
  }

  if (safeDetail) {
    return `请求失败：${safeDetail}`;
  }

  return "请求失败，请稍后重试。";
}

export async function analyzePullRequest(payload: ReviewRequest): Promise<ReviewResponse> {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(`${getApiBaseUrl()}/api/review`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        pr_url: payload.pr_url,
        github_token: payload.github_token || "",
        use_ai: payload.use_ai,
      }),
      signal: controller.signal,
    });

    const responseData = await response.json().catch(() => ({}));

    if (!response.ok) {
      const detail = extractErrorDetail(responseData);
      throw new Error(mapBackendError(response.status, detail));
    }

    return responseData as ReviewResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("无法连接后端服务，请确认 FastAPI 已在 http://127.0.0.1:8000 启动。");
    }

    if (error instanceof TypeError) {
      throw new Error("无法连接后端服务，请确认 FastAPI 已在 http://127.0.0.1:8000 启动。");
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error("请求失败，请稍后重试。");
  } finally {
    window.clearTimeout(timeoutId);
  }
}
