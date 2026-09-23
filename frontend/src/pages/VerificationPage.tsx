import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ShieldAlert, CheckCircle2, XCircle, RotateCcw, MapPin, Clock3, UserCircle2 } from "lucide-react";
import { useInspectionFlow } from "../hooks/useInspectionFlow";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { SeverityPill } from "../components/SeverityPill";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { cn } from "../utils/cn";

type DecisionType = "Confirmed" | "Marked Compliant" | "Re-analysis Requested";

export default function VerificationPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { active, decisions, recordDecision, finalize } = useInspectionFlow();
  const { push } = useToast();
  const [activeIdx, setActiveIdx] = useState(0);
  const [overrideText, setOverrideText] = useState("");
  const [showOverride, setShowOverride] = useState<DecisionType | null>(null);

  const issues = active?.rules.filter((r) => r.status !== "Compliant") ?? [];

  useEffect(() => { if (!active) navigate("/scan"); }, [active, navigate]);
  if (!active) return null;

  const current = issues[activeIdx];
  const currentDecision = current ? decisions.find((d) => d.ruleId === current.ruleId) : undefined;

  const decide = (type: DecisionType, needsReason: boolean) => {
    if (!current) return;
    if (needsReason && !currentDecision) {
      setShowOverride(type);
      return;
    }
    recordDecision({ ruleId: current.ruleId, decision: type });
    push("success", `Marked as "${type}"`, current.name);
    if (activeIdx < issues.length - 1) setActiveIdx((i) => i + 1);
  };

  const confirmOverride = () => {
    if (!current || overrideText.trim().length < 8) {
      push("error", "Reason required", "Please describe why you are overriding the AI recommendation (min. 8 characters).");
      return;
    }
    recordDecision({ ruleId: current.ruleId, decision: showOverride!, overrideReason: overrideText.trim() });
    push("success", `Override recorded`, current.name);
    setOverrideText("");
    setShowOverride(null);
    if (activeIdx < issues.length - 1) setActiveIdx((i) => i + 1);
  };

  const allDecided = issues.length === 0 || decisions.filter((d) => issues.some((i) => i.ruleId === d.ruleId)).length >= issues.length;

  const handleFinalize = () => {
    const insp = finalize();
    if (insp) {
      push("success", "Inspection finalized", `Report generated for ${insp.scanId}`);
      navigate(`/report/${insp.scanId}`);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-text-1">Inspector Verification</h1>
        <p className="mt-1 text-sm text-text-2">Scan ID {active.scanId} · {active.product}</p>
      </div>

      <div className="flex items-start gap-3 rounded-xl border border-warn-500/30 bg-warn-50 p-4">
        <ShieldAlert size={18} className="mt-0.5 shrink-0 text-warn-600" />
        <p className="text-sm text-warn-600">
          AI provides recommendations. Final compliance decisions must be verified by an authorized inspector.
        </p>
      </div>

      {issues.length === 0 ? (
        <div className="rounded-xl border border-ok-500/30 bg-ok-50 p-8 text-center">
          <CheckCircle2 size={28} className="mx-auto text-ok-600" />
          <p className="mt-2 font-display text-sm font-bold text-ok-600">No potential issues detected</p>
          <p className="mt-1 text-xs text-text-2">This inspection is ready to be finalized directly.</p>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-2">
            {issues.map((iss, i) => {
              const d = decisions.find((x) => x.ruleId === iss.ruleId);
              return (
                <button
                  key={iss.ruleId}
                  onClick={() => setActiveIdx(i)}
                  className={cn(
                    "flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors",
                    i === activeIdx ? "border-cyan-500 bg-cyan-50 text-cyan-700" : "border-line bg-white text-text-2",
                    d && "opacity-70"
                  )}
                >
                  {d ? <CheckCircle2 size={13} className="text-ok-600" /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                  Issue #{pad(i + 1)}
                </button>
              );
            })}
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <div className="rounded-xl border border-line bg-paper-card p-4">
              <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-text-3">Evidence image</p>
              <div className="relative overflow-hidden rounded-lg">
                <img src={active.image} className="w-full object-cover" style={{ aspectRatio: "4/5" }} />
                <div className="absolute animate-pulse-ring rounded-sm border-2 border-bad-500 bg-bad-500/10" style={{ left: "8%", top: "46%", width: "45%", height: "7%" }} />
              </div>
            </div>

            <div className="rounded-xl border border-line bg-paper-card p-5">
              <p className="text-xs font-semibold uppercase tracking-wide text-text-3">AI finding</p>
              <p className="mt-1 font-display text-lg font-bold text-text-1">Potential Issue #{pad(activeIdx + 1)}</p>
              <p className="mt-0.5 text-sm text-text-2">{current?.name}</p>

              <div className="mt-3 flex items-center gap-3">
                <ConfidenceBadge value={current?.confidence ?? 0} />
                {current && <SeverityPill severity={current.severity} />}
              </div>

              <p className="mt-3 rounded-md bg-paper px-3 py-2 font-code text-xs text-text-2">"{current?.evidence}"</p>

              <p className="mt-4 mb-2 text-xs font-semibold uppercase tracking-wide text-text-3">Inspector decision</p>

              {currentDecision ? (
                <div className="rounded-lg border border-ok-500/30 bg-ok-50 p-3">
                  <p className="text-sm font-semibold text-ok-600">Recorded: {currentDecision.decision}</p>
                  {currentDecision.overrideReason && <p className="mt-1 text-xs text-text-2">Reason: {currentDecision.overrideReason}</p>}
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <button onClick={() => decide("Confirmed", false)} className="flex items-center justify-center gap-1.5 rounded-lg border border-bad-500/30 bg-bad-50 py-2.5 text-xs font-semibold text-bad-600 hover:bg-bad-500/10">
                    <XCircle size={14} /> Confirm Issue
                  </button>
                  <button onClick={() => decide("Marked Compliant", true)} className="flex items-center justify-center gap-1.5 rounded-lg border border-ok-500/30 bg-ok-50 py-2.5 text-xs font-semibold text-ok-600 hover:bg-ok-500/10">
                    <CheckCircle2 size={14} /> Mark Compliant
                  </button>
                  <button onClick={() => decide("Re-analysis Requested", true)} className="flex items-center justify-center gap-1.5 rounded-lg border border-signal-500/30 bg-signal-500/10 py-2.5 text-xs font-semibold text-signal-500 hover:bg-signal-500/20">
                    <RotateCcw size={14} /> Request Re-analysis
                  </button>
                </div>
              )}

              {showOverride && (
                <div className="mt-3 rounded-lg border border-line bg-paper p-3">
                  <p className="mb-1.5 text-xs font-semibold text-text-1">Mandatory override reason</p>
                  <textarea
                    value={overrideText}
                    onChange={(e) => setOverrideText(e.target.value)}
                    placeholder="Enter reason for overriding AI recommendation…"
                    rows={3}
                    className="w-full rounded-md border border-line bg-white px-2.5 py-2 text-xs text-text-1 focus-ring focus:border-cyan-500"
                  />
                  <div className="mt-2 flex justify-end gap-2">
                    <button onClick={() => { setShowOverride(null); setOverrideText(""); }} className="rounded-md px-3 py-1.5 text-xs font-medium text-text-2 hover:bg-white">Cancel</button>
                    <button onClick={confirmOverride} className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-ink-800">Submit reason</button>
                  </div>
                </div>
              )}

              <div className="mt-5 space-y-2 border-t border-line pt-4 text-xs text-text-2">
                <div className="flex items-center gap-2"><UserCircle2 size={13} /> Inspector ID: {user?.id}</div>
                <div className="flex items-center gap-2"><Clock3 size={13} /> {new Date().toLocaleString("en-IN")}</div>
                <div className="flex items-center gap-2"><MapPin size={13} /> {active.location}</div>
              </div>
            </div>
          </div>
        </>
      )}

      <div className="flex justify-end">
        <button
          onClick={handleFinalize}
          disabled={!allDecided}
          className="flex items-center gap-2 rounded-lg bg-ink-900 px-5 py-2.5 text-sm font-semibold text-white hover:bg-ink-800 disabled:opacity-50"
        >
          Finalize Inspection
        </button>
      </div>
    </div>
  );
}

function pad(n: number) { return String(n).padStart(2, "0"); }
