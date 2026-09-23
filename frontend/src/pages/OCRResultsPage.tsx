import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { RefreshCw, Pencil, ArrowRight, Check } from "lucide-react";
import { useInspectionFlow } from "../hooks/useInspectionFlow";
import { useToast } from "../hooks/useToast";
import { ConfidenceBadge } from "../components/ConfidenceBadge";
import { cn } from "../utils/cn";

const PIPELINE = ["Image Processing", "OCR", "Language Detection", "Field Extraction", "Rule Matching"];

const BOX_COLORS: Record<string, string> = {
  MRP: "border-cyan-400",
  "Net Quantity": "border-violet-400",
  Manufacturer: "border-signal-500",
  "Manufacturing Date": "border-warn-500",
  "Best Before": "border-warn-500",
  "Consumer Care": "border-bad-500",
  "Batch Number": "border-ok-500",
};

export default function OCRResultsPage() {
  const navigate = useNavigate();
  const { active, generateInspection, updateExtractedField } = useInspectionFlow();
  const { push } = useToast();
  const [pipelineStep, setPipelineStep] = useState(0);
  const [done, setDone] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const [hovered, setHovered] = useState<string | null>(null);

  useEffect(() => {
    if (!active) { navigate("/scan"); return; }
    setPipelineStep(0);
    setDone(false);
    const iv = setInterval(() => {
      setPipelineStep((p) => {
        if (p >= PIPELINE.length - 1) {
          clearInterval(iv);
          setDone(true);
          return p;
        }
        return p + 1;
      });
    }, 480);
    return () => clearInterval(iv);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active?.scanId]);

  if (!active) return null;

  const rerunOcr = () => {
    generateInspection();
    push("info", "OCR re-run started", "Re-processing the same images with the OCR engine.");
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-text-1">AI Analysis {done ? "Complete" : "in Progress"}</h1>
        <p className="mt-1 text-sm text-text-2">Scan ID {active.scanId} · {active.product}</p>
      </div>

      <div className="rounded-xl border border-line bg-paper-card p-5">
        <div className="flex flex-wrap items-center gap-2">
          {PIPELINE.map((step, i) => (
            <div key={step} className="flex items-center gap-2">
              <div
                className={cn(
                  "flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors",
                  i < pipelineStep || done ? "border-ok-500/40 bg-ok-50 text-ok-600" :
                  i === pipelineStep ? "border-cyan-500/40 bg-cyan-50 text-cyan-600 animate-pulse-ring" :
                  "border-line bg-paper text-text-3"
                )}
              >
                {(i < pipelineStep || done) ? <Check size={13} /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
                {step}
              </div>
              {i < PIPELINE.length - 1 && <ArrowRight size={13} className="text-text-3" />}
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-line bg-paper-card p-4">
          <h3 className="mb-3 font-display text-sm font-bold text-text-1">Label with detected fields</h3>
          <div className="relative overflow-hidden rounded-lg">
            <img src={active.image} alt={active.product} className="w-full object-cover" style={{ aspectRatio: "4/5" }} />
            {done && active.extracted.map((f) => (
              <div
                key={f.label}
                onMouseEnter={() => setHovered(f.label)}
                onMouseLeave={() => setHovered(null)}
                className={cn(
                  "absolute rounded-sm border-2 transition-all",
                  BOX_COLORS[f.label] ?? "border-cyan-400",
                  hovered === f.label ? "bg-white/10 shadow-lg" : ""
                )}
                style={{ left: `${f.box.x}%`, top: `${f.box.y}%`, width: `${f.box.w}%`, height: `${f.box.h}%` }}
              >
                <span className="absolute -top-5 left-0 rounded bg-ink-900/90 px-1.5 py-0.5 text-[9px] font-semibold text-white">
                  {f.label}
                </span>
              </div>
            ))}
            {!done && <div className="absolute inset-x-0 top-0 h-1 animate-scan-sweep bg-gradient-to-r from-cyan-400 to-violet-400" />}
          </div>
        </div>

        <div className="rounded-xl border border-line bg-paper-card p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-display text-sm font-bold text-text-1">Extracted information</h3>
            <button onClick={rerunOcr} className="flex items-center gap-1.5 text-xs font-semibold text-cyan-600 hover:underline">
              <RefreshCw size={13} /> Re-run OCR
            </button>
          </div>
          <div className="space-y-2">
            {active.extracted.map((f) => (
              <div
                key={f.label}
                onMouseEnter={() => setHovered(f.label)}
                onMouseLeave={() => setHovered(null)}
                className={cn(
                  "rounded-lg border p-3 transition-colors",
                  hovered === f.label ? "border-cyan-400 bg-cyan-50/40" : "border-line"
                )}
              >
                <div className="flex items-center justify-between">
                  <p className="text-xs font-semibold text-text-2">{f.label}</p>
                  <ConfidenceBadge value={f.confidence} />
                </div>
                {editing === f.label ? (
                  <input
                    autoFocus
                    defaultValue={f.value}
                    onBlur={(e) => { updateExtractedField(f.label, e.target.value); setEditing(null); }}
                    onKeyDown={(e) => { if (e.key === "Enter") (e.target as HTMLInputElement).blur(); }}
                    className="mt-1 w-full rounded-md border border-cyan-400 px-2 py-1 text-sm font-medium text-text-1 focus:outline-none"
                  />
                ) : (
                  <button onClick={() => setEditing(f.label)} className="mt-1 flex w-full items-center justify-between text-left">
                    <span className="font-tabular text-sm font-semibold text-text-1">{f.value}</span>
                    <Pencil size={12} className="text-text-3" />
                  </button>
                )}
              </div>
            ))}
          </div>

          <button
            disabled={!done}
            onClick={() => navigate("/compliance")}
            className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-ink-900 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-ink-800 disabled:opacity-50"
          >
            Continue to Compliance Check <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </div>
  );
}
