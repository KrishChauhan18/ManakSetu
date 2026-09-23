import type { ResultStatus } from "../types";
import { statusTone } from "../utils/format";
import { cn } from "../utils/cn";

export function StatusBadge({ status, className }: { status: ResultStatus; className?: string }) {
  const t = statusTone[status];
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold", t.bg, t.text, t.border, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", t.dot)} />
      {status}
    </span>
  );
}
