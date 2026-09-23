import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  Download,
  FileJson,
  FileSpreadsheet,
  Printer,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  ChevronLeft,
  ShieldCheck,
  XCircle,
} from "lucide-react";
import {
  apiGetScan,
  getPdfUrl,
  getCsvUrl,
  getJsonUrl,
  getScanImageUrl,
  type ScanRecord,
  type Violation,
} from "../services/api";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border-red-200",
  high: "bg-orange-100 text-orange-700 border-orange-200",
  medium: "bg-yellow-100 text-yellow-700 border-yellow-200",
  low: "bg-blue-100 text-blue-700 border-blue-200",
  manual_review: "bg-purple-100 text-purple-700 border-purple-200",
};

function ComplianceBadge({ pct }: { pct: number }) {
  if (pct >= 100)
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-green-100 px-3 py-1 text-xs font-semibold text-green-800 ring-1 ring-green-200">
        <CheckCircle2 className="h-3.5 w-3.5" />
        Fully Compliant
      </span>
    );
  if (pct >= 80)
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-yellow-100 px-3 py-1 text-xs font-semibold text-yellow-800 ring-1 ring-yellow-200">
        <Clock3 className="h-3.5 w-3.5" />
        Partially Compliant
      </span>
    );
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-800 ring-1 ring-red-200">
      <XCircle className="h-3.5 w-3.5" />
      Non-Compliant
    </span>
  );
}

function ViolationCard({ v }: { v: Violation }) {
  return (
    <div
      className={`rounded-xl border p-4 ${SEVERITY_COLORS[v.severity] ?? "bg-slate-50 text-slate-700 border-slate-200"}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-bold uppercase tracking-wide opacity-70">
            {v.rule_id} · {v.legal_rule_ref}
          </p>
          <p className="mt-1 font-semibold">{v.field}</p>
        </div>
        <span className="rounded-full border px-2 py-0.5 text-[11px] font-bold uppercase">
          {v.severity}
        </span>
      </div>
      <p className="mt-2 text-sm opacity-90">{v.message}</p>
      {v.detected_value && (
        <p className="mt-1 text-xs opacity-70">
          Detected: <strong>{v.detected_value}</strong>
          {v.expected && (
            <>
              {" "}
              · Expected: <strong>{v.expected}</strong>
            </>
          )}
        </p>
      )}
      {v.recommendation && (
        <p className="mt-2 rounded-lg bg-white/60 px-3 py-2 text-xs font-medium">
          💡 {v.recommendation}
        </p>
      )}
    </div>
  );
}

export default function ReportPage() {
  const { scanId = "" } = useParams();

  const [scan, setScan] = useState<ScanRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!scanId) return;
    setLoading(true);
    setError("");
    apiGetScan(scanId)
      .then((s) => setScan(s))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load report")
      )
      .finally(() => setLoading(false));
  }, [scanId]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-orange-100 border-t-[#f5a623]" />
          <p className="mt-3 text-sm text-slate-500">Loading report…</p>
        </div>
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="rounded-xl border border-red-100 bg-red-50 p-10 text-center">
        <AlertTriangle className="mx-auto h-10 w-10 text-red-400" />
        <p className="mt-3 font-semibold text-red-700">
          {error || `Report not found for scan ID ${scanId}.`}
        </p>
        <Link
          to="/history"
          className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-blue-600 hover:underline"
        >
          <ChevronLeft className="h-4 w-4" /> Back to History
        </Link>
      </div>
    );
  }

  const pdfUrl = getPdfUrl(scan.id);
  const csvUrl = getCsvUrl(scan.id);
  const jsonUrl = getJsonUrl(scan.id);
  const imageUrl = getScanImageUrl(scan.id);
  const annotatedUrl = getScanImageUrl(scan.id, true);
  const createdAt = scan.created_at
    ? new Date(scan.created_at).toLocaleString()
    : "Unknown";

  const labelFields = Object.entries(scan.label_record ?? {}).filter(
    ([k, v]) =>
      typeof v === "object" &&
      v !== null &&
      "value" in (v as object) &&
      !["quality_assessment", "raw_ocr_text", "language_detected"].includes(k)
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="mb-1 flex items-center gap-2">
            <Link
              to="/history"
              className="flex items-center gap-1 text-xs text-slate-400 hover:text-slate-700"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Back to History
            </Link>
          </div>
          <h1 className="font-display text-2xl font-bold text-slate-900">
            Inspection Report
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            Scan #{scan.id} · {scan.category?.toUpperCase()} · {createdAt}
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <a
            href={pdfUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3.5 py-2 text-xs font-semibold text-white hover:bg-slate-700"
          >
            <Download size={14} /> Download PDF
          </a>
          <a
            href={jsonUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <FileJson size={14} /> Export JSON
          </a>
          <a
            href={csvUrl}
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <FileSpreadsheet size={14} /> Export CSV
          </a>
          <button
            onClick={() => window.print()}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
          >
            <Printer size={14} /> Print
          </button>
        </div>
      </div>

      {/* Compliance Score Card */}
      <div className="rounded-2xl bg-gradient-to-br from-[#FFF1DC] to-[#FFF8EC] p-6 shadow-sm ring-1 ring-orange-100">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-slate-500">
              Overall Compliance Score
            </p>
            <p className="mt-1 text-5xl font-bold text-[#173b68]">
              {scan.compliance_pct?.toFixed(1)}%
            </p>
            <div className="mt-2">
              <ComplianceBadge pct={scan.compliance_pct} />
            </div>
          </div>
          <div className="flex flex-col items-end gap-2 text-sm text-slate-600">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800">
                {scan.violations.filter((v) =>
                  ["critical", "high"].includes(v.severity)
                ).length}
              </span>{" "}
              critical/high violations
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800">
                {scan.violations.length}
              </span>{" "}
              total violations
            </div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800">
                {scan.status}
              </span>{" "}
              status
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-4 h-3 w-full overflow-hidden rounded-full bg-orange-100">
          <div
            className="h-full rounded-full bg-gradient-to-r from-[#f5a623] to-[#22c55e] transition-all duration-700"
            style={{ width: `${Math.min(scan.compliance_pct, 100)}%` }}
          />
        </div>
      </div>

      {/* Images */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <p className="border-b border-slate-100 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Original Image
          </p>
          <img
            src={imageUrl}
            alt="Original scan"
            className="h-56 w-full object-contain bg-slate-50"
            onError={(e) =>
              ((e.target as HTMLImageElement).src =
                "https://placehold.co/400x300?text=No+Image")
            }
          />
        </div>
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
          <p className="border-b border-slate-100 px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            Annotated (AI Evidence)
          </p>
          <img
            src={annotatedUrl}
            alt="Annotated scan"
            className="h-56 w-full object-contain bg-slate-50"
            onError={(e) =>
              ((e.target as HTMLImageElement).src =
                "https://placehold.co/400x300?text=No+Annotation")
            }
          />
        </div>
      </div>

      {/* Extracted fields */}
      {labelFields.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-base font-bold text-slate-800">
            Extracted Label Declarations
          </h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {labelFields.map(([key, val]) => {
              const fv = val as { value?: unknown; confidence?: number; source?: string };
              return (
                <div
                  key={key}
                  className="rounded-lg border border-slate-100 bg-slate-50 p-3"
                >
                  <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                    {key.replace(/_/g, " ")}
                  </p>
                  <p className="mt-0.5 truncate text-sm font-medium text-slate-800">
                    {String(fv.value ?? "N/A")}
                  </p>
                  {fv.confidence !== undefined && (
                    <p className="mt-0.5 text-[11px] text-slate-400">
                      Confidence: {((fv.confidence ?? 0) * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Violations */}
      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-800">
            Rule Violations &amp; Legal Remedies
          </h2>
          {scan.violations.length === 0 && (
            <span className="flex items-center gap-1.5 text-xs font-semibold text-green-600">
              <ShieldCheck className="h-4 w-4" /> No violations
            </span>
          )}
        </div>

        {scan.violations.length === 0 ? (
          <div className="rounded-xl border border-dashed border-green-200 bg-green-50 px-6 py-10 text-center">
            <ShieldCheck className="mx-auto h-10 w-10 text-green-400" />
            <p className="mt-3 text-sm font-semibold text-green-700">
              All statutory declarations satisfied
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {scan.violations.map((v) => (
              <ViolationCard key={v.id} v={v} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}