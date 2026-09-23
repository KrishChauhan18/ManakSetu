import type { ResultStatus, Severity } from "../types";

export function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

export function formatDateTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleString("en-IN", { day: "2-digit", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

export function timeAgo(iso: string) {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

export const statusTone: Record<ResultStatus, { bg: string; text: string; border: string; dot: string }> = {
  "Compliant": { bg: "bg-ok-50", text: "text-ok-600", border: "border-ok-500/30", dot: "bg-ok-500" },
  "Review Required": { bg: "bg-warn-50", text: "text-warn-600", border: "border-warn-500/30", dot: "bg-warn-500" },
  "Potential Issue": { bg: "bg-bad-50", text: "text-bad-600", border: "border-bad-500/30", dot: "bg-bad-500" },
};

export const severityTone: Record<Severity, { bg: string; text: string }> = {
  Critical: { bg: "bg-bad-50", text: "text-bad-600" },
  High: { bg: "bg-warn-50", text: "text-warn-600" },
  Medium: { bg: "bg-signal-500/10", text: "text-signal-500" },
  Low: { bg: "bg-ink-700/10", text: "text-text-2" },
};

export function confidenceTone(v: number) {
  if (v >= 90) return { text: "text-ok-600", bg: "bg-ok-500", track: "bg-ok-50" };
  if (v >= 75) return { text: "text-warn-600", bg: "bg-warn-500", track: "bg-warn-50" };
  return { text: "text-bad-600", bg: "bg-bad-500", track: "bg-bad-50" };
}
