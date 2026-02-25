import type { AnalyzeRequest, AnalyzeResponse } from "./types";

const BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() ||
  (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

export async function analyzeChatLog(payload: AnalyzeRequest): Promise<AnalyzeResponse> {
  const response = await fetch(`${BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "분석 요청 실패");
  }

  return response.json() as Promise<AnalyzeResponse>;
}

export async function exportAnalysisFile(payload: {
  analysis: AnalyzeRequest;
  format: "json" | "csv";
  dataset: "summary" | "highlights" | "volume" | "keywords" | "parse_errors" | "all";
}): Promise<void> {
  const response = await fetch(`${BASE_URL}/api/export`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "내보내기 요청 실패");
  }

  const disposition = response.headers.get("Content-Disposition") ?? "";
  const matched = disposition.match(/filename="?([^\"]+)"?/);
  const filename = matched?.[1] ?? `analysis.${payload.format}`;
  const blob = await response.blob();

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
