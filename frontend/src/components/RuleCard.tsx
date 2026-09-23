import { useState } from "react";
import { ChevronDown, CheckCircle2, AlertTriangle, XCircle, Eye } from "lucide-react";
import type { RuleCheck } from "../types";
import { SeverityPill } from "./SeverityPill";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { statusTone } from "../utils/format";
import { cn } from "../utils/cn";

const ICON = { "Compliant": CheckCircle2, "Review Required": AlertTriangle, "Potential Issue": XCircle };

export function RuleCard({ rule, onViewEvidence }: { rule: RuleCheck; onViewEvidence?: (rule: RuleCheck) => void }) {
  const [open, setOpen] = useState(rule.status !== "Compliant");
  const tone = statusTone[rule.status];
  const Icon = ICON[rule.status];

  return (
    <div
      className="overflow-hidden rounded-lg border border-line border-l-4 bg-paper-card"
      style={{ borderLeftColor: `var(--color-${rule.status === "Compliant" ? "ok" : rule.status === "Review Required" ? "warn" : "bad"}-500)` }}
    >
      <button onClick={() => setOpen((v) => !v)} className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left">
        <div className="flex min-w-0 items-center gap-3">
          <Icon size={18} className={tone.text} />
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-text-1">{rule.name}</p>
            <p className="font-code text-[11px] text-text-3">{rule.ruleId} · {rule.category}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <SeverityPill severity={rule.severity} />
          <span className={cn("hidden rounded-full px-2.5 py-1 text-xs font-semibold sm:inline", tone.bg, tone.text)}>{rule.status}</span>
          <ChevronDown size={16} className={cn("text-text-3 transition-transform", open && "rotate-180")} />
        </div>
      </button>
      {open && (
        <div className="border-t border-line px-4 py-3">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Confidence</p>
              <div className="mt-1"><ConfidenceBadge value={rule.confidence} /></div>
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Severity</p>
              <div className="mt-1"><SeverityPill severity={rule.severity} /></div>
            </div>
            <div className="sm:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Evidence</p>
              <p className="mt-1 rounded-md bg-paper px-2.5 py-1.5 font-code text-xs text-text-2">"{rule.evidence}"</p>
            </div>
            <div className="sm:col-span-2">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Recommendation</p>
              <p className="mt-1 text-xs text-text-2">{rule.recommendation}</p>
            </div>
          </div>
          {rule.status !== "Compliant" && onViewEvidence && (
            <button
              onClick={() => onViewEvidence(rule)}
              className="mt-3 flex items-center gap-1.5 rounded-md border border-line bg-white px-3 py-1.5 text-xs font-semibold text-text-1 hover:bg-paper"
            >
              <Eye size={13} /> View Evidence
            </button>
          )}
        </div>
      )}
    </div>
  );
}
