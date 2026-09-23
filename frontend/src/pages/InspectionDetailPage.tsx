import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { useInspectionFlow } from "../hooks/useInspectionFlow";
import { buildAuditTrail } from "../data/mockData";
import { StatusBadge } from "../components/StatusBadge";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { RuleCard } from "../components/RuleCard";
import { ComplianceScore } from "../components/ComplianceScore";
import { AuditTimeline } from "../components/AuditTimeline";
import { formatDateTime } from "../utils/format";
import { cn } from "../utils/cn";

const TABS = ["Overview", "Product Images", "OCR Results", "Compliance", "Evidence", "Report", "Audit"] as const;

export default function InspectionDetailPage() {
  const { scanId = "" } = useParams();
  const navigate = useNavigate();
  const { getInspection } = useInspectionFlow();
  const [tab, setTab] = useState<(typeof TABS)[number]>("Overview");
  const insp = getInspection(scanId);
  const events = useMemo(() => insp ? buildAuditTrail(insp.scanId, insp.officer, insp.date) : [], [insp]);

  if (!insp) {
    // If it's a real backend scan ID, direct to ReportPage
    return (
      <div className="rounded-xl border border-line bg-paper-card p-10 text-center text-sm text-text-2 space-y-3">
        <p>Loading inspection {scanId} details...</p>
        <button
          onClick={() => navigate(`/report/${scanId}`)}
          className="inline-flex items-center gap-1.5 rounded-lg bg-orange-600 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-700"
        >
          View Full Inspection Report <ExternalLink size={14} />
        </button>
      </div>
    );
  }

  const issues = insp.rules.filter((r) => r.status !== "Compliant");

  return (
    <div className="space-y-6">
      <button onClick={() => navigate(-1)} className="flex items-center gap-1.5 text-xs font-semibold text-text-2 hover:text-text-1">
        <ArrowLeft size={14} /> Back
      </button>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-bold text-text-1">{insp.product}</h1>
          <p className="mt-1 text-sm text-text-2">{insp.scanId} · {insp.manufacturer} · {insp.category}</p>
        </div>
        <StatusBadge status={insp.result} />
      </div>

      <div className="flex gap-1 overflow-x-auto rounded-lg border border-line bg-paper-card p-1">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn("whitespace-nowrap rounded-md px-3.5 py-2 text-xs font-semibold transition-colors", tab === t ? "bg-ink-900 text-white" : "text-text-2 hover:bg-paper")}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Overview" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="flex flex-col items-center justify-center rounded-xl border border-line bg-paper-card p-6">
            <ComplianceScore score={insp.score} size={140} />
          </div>
          <div className="rounded-xl border border-line bg-paper-card p-5 lg:col-span-2">
            <h3 className="mb-3 font-display text-sm font-bold text-text-1">Inspection details</h3>
            <div className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
              {[["Officer", insp.officer], ["Region", insp.region], ["Location", insp.location], ["Date", formatDateTime(insp.date)], ["Rules passed", `${insp.rules.filter((r) => r.status === "Compliant").length}/${insp.rules.length}`], ["Open issues", String(issues.length)]].map(([k, v]) => (
                <div key={k}>
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-text-3">{k}</p>
                  <p className="mt-1 font-medium text-text-1">{v}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "Product Images" && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          {["Front", "Back", "Side"].map((label) => (
            <div key={label} className="overflow-hidden rounded-xl border border-line bg-paper-card">
              <img src={insp.image} className="h-44 w-full object-cover" />
              <p className="p-2.5 text-center text-xs font-semibold text-text-2">{label}</p>
            </div>
          ))}
        </div>
      )}

      {tab === "OCR Results" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {insp.extracted.map((f) => (
            <div key={f.label} className="rounded-lg border border-line bg-paper-card p-3">
              <p className="text-xs font-semibold text-text-2">{f.label}</p>
              <div className="mt-1 flex items-center justify-between">
                <span className="font-tabular text-sm font-semibold text-text-1">{f.value}</span>
                <ConfidenceBadge value={f.confidence} />
              </div>
            </div>
          ))}
        </div>
      )}

      {tab === "Compliance" && (
        <div className="space-y-2.5">
          {insp.rules.map((r) => <RuleCard key={r.ruleId} rule={r} />)}
        </div>
      )}

      {tab === "Evidence" && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="relative overflow-hidden rounded-xl">
            <img src={insp.image} className="w-full object-cover" style={{ aspectRatio: "4/5" }} />
            {issues.map((_, i) => (
              <div key={i} className="absolute rounded-sm border-2 border-bad-500 bg-bad-500/10" style={{ left: `${8 + i * 5}%`, top: `${40 + i * 12}%`, width: "40%", height: "7%" }} />
            ))}
          </div>
          <div className="space-y-2">
            {issues.length === 0 && <p className="text-sm text-text-2">No flagged evidence for this inspection.</p>}
            {issues.map((r) => (
              <div key={r.ruleId} className="rounded-lg border border-line bg-paper-card p-3">
                <p className="text-sm font-semibold text-text-1">{r.name}</p>
                <p className="mt-1 font-code text-xs text-text-2">"{r.evidence}"</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === "Report" && (
        <div className="rounded-xl border border-line bg-paper-card p-6 text-center">
          <p className="text-sm text-text-2">Open the full formatted inspection report.</p>
          <button onClick={() => navigate(`/report/${insp.scanId}`)} className="mt-3 inline-flex items-center gap-1.5 rounded-lg bg-ink-900 px-4 py-2 text-sm font-semibold text-white hover:bg-ink-800">
            Open report <ExternalLink size={14} />
          </button>
        </div>
      )}

      {tab === "Audit" && <AuditTimeline events={events} />}
    </div>
  );
}
