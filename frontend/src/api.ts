import type { ReviewRequest, ReviewResponse } from "./types";

const DEFAULT_API_BASE = "http://127.0.0.1:8000";
const REQUEST_TIMEOUT_MS = 120000;

function getApiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL || DEFAULT_API_BASE).replace(/\/$/, "");
}

function extractErrorMessage(payload: unknown): string {
  if (!payload || typeof payload !== "object") {
    return "Request failed.";
  }

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    const nested = (detail as { message?: unknown }).message;
    if (typeof nested === "string") {
      return nested;
    }
  }

  return "Request failed.";
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

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(extractErrorMessage(data));
    }

    return data as ReviewResponse;
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error("Request timed out. Please check whether backend is running and try again.");
    }
    if (error instanceof TypeError) {
      throw new Error("Failed to connect to backend. Please check whether backend is running.");
    }
    if (error instanceof Error) {
      throw error;
    }
    throw new Error("Unexpected error occurred while calling backend API.");
  } finally {
    window.clearTimeout(timeoutId);
  }
}
