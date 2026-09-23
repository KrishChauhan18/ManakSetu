import type { Severity } from "../types";
import { severityTone } from "../utils/format";
import { cn } from "../utils/cn";

export function SeverityPill({ severity }: { severity: Severity }) {
  const t = severityTone[severity];
  return (
    <span className={cn("rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide", t.bg, t.text)}>
      {severity}
    </span>
  );
}
