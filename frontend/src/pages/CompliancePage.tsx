import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, ListChecks } from "lucide-react";
import { useInspectionFlow } from "../hooks/useInspectionFlow";
import { ComplianceScore } from "../components/ComplianceScore";
import { RuleCard } from "../components/RuleCard";
import { Modal } from "../components/Modal";
import { useState } from "react";
import type { RuleCheck } from "../types";

export default function CompliancePage() {
  const navigate = useNavigate();
  const { active } = useInspectionFlow();
  const [evidence, setEvidence] = useState<RuleCheck | null>(null);

  useEffect(() => { if (!active) navigate("/scan"); }, [active, navigate]);
  if (!active) return null;

  const passCount = active.rules.filter((r) => r.status === "Compliant").length;
  const issueCount = active.rules.filter((r) => r.status !== "Compliant").length;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-text-1">Compliance Analysis</h1>
        <p className="mt-1 text-sm text-text-2">Scan ID {active.scanId} · {active.product}</p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="flex flex-col items-center justify-center rounded-xl border border-line bg-paper-card p-6">
          <ComplianceScore score={active.score} />
          <p className="mt-4 text-center text-xs text-text-2">Overall compliance score based on {active.rules.length} weighted Legal Metrology rules</p>
        </div>
        <div className="flex flex-col justify-center gap-4 rounded-xl border border-line bg-paper-card p-6 lg:col-span-2">
          <div className="flex items-center gap-2">
            <ListChecks size={16} className="text-cyan-600" />
            <h3 className="font-display text-sm font-bold text-text-1">Rule validation summary</h3>
          </div>
          <div className="grid grid-cols-3 gap-3">
            <div className="rounded-lg bg-ok-50 p-3">
              <p className="font-display text-2xl font-bold text-ok-600">{passCount}</p>
              <p className="text-xs text-text-2">Rules passed</p>
            </div>
            <div className="rounded-lg bg-warn-50 p-3">
              <p className="font-display text-2xl font-bold text-warn-600">{active.rules.filter((r) => r.status === "Review Required").length}</p>
              <p className="text-xs text-text-2">Review required</p>
            </div>
            <div className="rounded-lg bg-bad-50 p-3">
              <p className="font-display text-2xl font-bold text-bad-600">{active.rules.filter((r) => r.status === "Potential Issue").length}</p>
              <p className="text-xs text-text-2">Potential issues</p>
            </div>
          </div>
          <p className="text-xs text-text-2">
            {issueCount > 0
              ? `${issueCount} finding${issueCount > 1 ? "s" : ""} require inspector attention before this inspection can be finalized.`
              : "All mandatory declarations satisfy the active rule set."}
          </p>
        </div>
      </div>

      <div>
        <h3 className="mb-3 font-display text-sm font-bold text-text-1">Rule validation</h3>
        <div className="space-y-2.5">
          {active.rules.map((rule) => (
            <RuleCard key={rule.ruleId} rule={rule} onViewEvidence={setEvidence} />
          ))}
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={() => navigate("/verify")}
          className="flex items-center gap-2 rounded-lg bg-ink-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-ink-800"
        >
          Continue to Inspector Verification <ArrowRight size={15} />
        </button>
      </div>

      <Modal open={!!evidence} onClose={() => setEvidence(null)} title="Evidence" subtitle={evidence?.ruleId} width="max-w-2xl">
        {evidence && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div className="relative overflow-hidden rounded-lg">
              <img src={active.image} className="w-full object-cover" style={{ aspectRatio: "4/5" }} />
              <div className="absolute rounded-sm border-2 border-bad-500 bg-bad-500/10" style={{ left: "8%", top: "46%", width: "45%", height: "7%" }} />
            </div>
            <div className="space-y-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Finding</p>
                <p className="mt-1 text-sm font-semibold text-text-1">{evidence.name}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Detected text</p>
                <p className="mt-1 rounded-md bg-paper px-2.5 py-1.5 font-code text-xs text-text-2">"{evidence.evidence}"</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">Recommendation</p>
                <p className="mt-1 text-xs text-text-2">{evidence.recommendation}</p>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
