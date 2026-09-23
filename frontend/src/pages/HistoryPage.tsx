import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  Search,
  SlidersHorizontal,
  ChevronRight,
} from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { apiListScans, type ScanRecord } from "../services/api";

interface BackendInspection {
  id: number;
  scan_id: string;
  inspector_id: number | null;
  product: string | null;
  category: string | null;
  manufacturer: string | null;
  result: string | null;
  score: number | null;
  region: string | null;
  location: string | null;
  image_url: string;
  image_public_id: string | null;
  extracted: unknown;
  rules: unknown;
  status: string;
  created_at: string;
  updated_at: string;
}

function mapScan(s: ScanRecord): BackendInspection {
  const rec = s.label_record ?? {};
  const mfr =
    (rec["manufacturer"] as { value?: string } | undefined)?.value ||
    (rec["manufacturer_name"] as { value?: string } | undefined)?.value ||
    null;
  const product =
    (rec["product_name"] as { value?: string } | undefined)?.value ||
    (rec["brand"] as { value?: string } | undefined)?.value ||
    null;
  let result: string | null = null;
  if (s.status === "done" && s.compliance_pct === 100) result = "Compliant";
  else if (s.status === "needs_review" || (s.violations && s.violations.length > 0)) result = "Review Required";
  else if (s.status === "processing") result = "Potential Issue";
  return {
    id: s.id,
    scan_id: String(s.id),
    inspector_id: s.user_id,
    product,
    category: s.category,
    manufacturer: mfr,
    result,
    score: s.compliance_pct,
    region: null,
    location: null,
    image_url: s.image_url,
    image_public_id: null,
    extracted: s.label_record,
    rules: null,
    status: s.status,
    created_at: s.created_at ?? new Date().toISOString(),
    updated_at: s.created_at ?? new Date().toISOString(),
  };
}

const RESULT_FILTERS = [
  "All",
  "Compliant",
  "Review Required",
  "Potential Issue",
] as const;

type ResultFilter = (typeof RESULT_FILTERS)[number];

function ResultBadge({ result }: { result: string | null }) {
  const styles: Record<string, string> = {
    Compliant: "bg-green-50 text-green-700",
    "Review Required": "bg-amber-50 text-amber-700",
    "Potential Issue": "bg-red-50 text-red-700",
    Uploaded: "bg-blue-50 text-blue-700",
  };

  const displayResult = result || "Uploaded";

  return (
    <span
      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
        styles[displayResult] || "bg-slate-50 text-slate-600"
      }`}
    >
      {displayResult}
    </span>
  );
}

export default function HistoryPage() {
  const { user } = useAuth();

  const [inspections, setInspections] = useState<
    BackendInspection[]
  >([]);

  const [query, setQuery] = useState("");
  const [resultFilter, setResultFilter] =
    useState<ResultFilter>("All");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchScans() {
      try {
        setLoading(true);
        setError("");
        const resp = await apiListScans({ page: 1, page_size: 100 });
        setInspections(resp.items.map(mapScan));
      } catch (err) {
        console.error("History fetch error:", err);
        setError(err instanceof Error ? err.message : "Could not load inspection history");
      } finally {
        setLoading(false);
      }
    }
    fetchScans();
  }, []);

  const filtered = useMemo(() => {
    return [...inspections]
      .filter(
        (inspection) =>
          resultFilter === "All" ||
          inspection.result === resultFilter
      )
      .filter((inspection) => {
        const q = query.trim().toLowerCase();

        if (!q) return true;

        return (
          (inspection.product || "")
            .toLowerCase()
            .includes(q) ||
          inspection.scan_id
            .toLowerCase()
            .includes(q) ||
          (inspection.manufacturer || "")
            .toLowerCase()
            .includes(q) ||
          String(inspection.inspector_id)
            .toLowerCase()
            .includes(q)
        );
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime()
      );
  }, [inspections, query, resultFilter]);

  if (!user) return null;

  const isInspector = user.role === "Inspector";

  return (
    <div className="space-y-5">

      {/* HEADER */}
      <div>
        <h1 className="text-xl font-bold text-slate-900">
          {isInspector
            ? "My Inspection History"
            : "Inspection History"}
        </h1>

        <p className="text-sm text-slate-500">
          {loading
            ? "Loading inspections..."
            : `${filtered.length} of ${inspections.length} inspections`}
        </p>
      </div>

      {/* ERROR */}
      {error && (
        <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-medium text-red-700">
          {error}
        </div>
      )}

      {/* SEARCH + FILTER */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />

          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by product, scan ID, manufacturer..."
            className="w-full rounded-xl border border-slate-200 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto">
          <SlidersHorizontal className="h-4 w-4 shrink-0 text-slate-400" />

          {RESULT_FILTERS.map((filter) => (
            <button
              key={filter}
              onClick={() => setResultFilter(filter)}
              className={`shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${
                resultFilter === filter
                  ? "border-blue-600 bg-blue-600 text-white"
                  : "border-slate-200 text-slate-600 hover:bg-slate-50"
              }`}
            >
              {filter}
            </button>
          ))}
        </div>
      </div>

      {/* TABLE */}
      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">

        {/* TABLE HEADER */}
        <div className="hidden grid-cols-12 gap-4 border-b border-slate-100 bg-slate-50 px-5 py-3 text-xs font-semibold text-slate-500 sm:grid">
          <div className="col-span-4">Product</div>

          <div className="col-span-2">
            Scan ID
          </div>

          {!isInspector && (
            <div className="col-span-2">
              Inspector
            </div>
          )}

          <div
            className={
              isInspector
                ? "col-span-3"
                : "col-span-2"
            }
          >
            Date
          </div>

          <div className="col-span-2">
            Result
          </div>

          <div className="col-span-1" />
        </div>

        {/* TABLE BODY */}
        <div className="divide-y divide-slate-50">

          {loading && (
            <p className="px-5 py-10 text-center text-sm text-slate-400">
              Loading inspection history...
            </p>
          )}

          {!loading &&
            filtered.map((inspection) => (
              <Link
                key={inspection.id}
                to={`/inspection/${inspection.id}`}
                className="grid grid-cols-12 items-center gap-4 px-5 py-3 text-sm hover:bg-slate-50"
              >

                {/* PRODUCT */}
                <div className="col-span-12 sm:col-span-4">
                  <p className="truncate font-medium text-slate-900">
                    {inspection.product ||
                      "Product analysis pending"}
                  </p>

                  <p className="truncate text-xs text-slate-500">
                    {inspection.manufacturer ||
                      "OCR data pending"}
                  </p>
                </div>

                {/* SCAN ID */}
                <div className="col-span-6 text-xs text-slate-500 sm:col-span-2">
                  {inspection.scan_id}
                </div>

                {/* INSPECTOR */}
                {!isInspector && (
                  <div className="col-span-6 text-xs text-slate-500 sm:col-span-2">
                    Inspector #{inspection.inspector_id}
                  </div>
                )}

                {/* DATE */}
                <div
                  className={`text-xs text-slate-500 ${
                    isInspector
                      ? "col-span-6 sm:col-span-3"
                      : "col-span-6 sm:col-span-2"
                  }`}
                >
                  {new Date(
                    inspection.created_at
                  ).toLocaleDateString("en-IN", {
                    day: "2-digit",
                    month: "short",
                    year: "numeric",
                  })}
                </div>

                {/* RESULT */}
                <div className="col-span-5 sm:col-span-2">
                  <ResultBadge
                    result={inspection.result}
                  />
                </div>

                {/* ARROW */}
                <div className="col-span-1 hidden justify-end sm:flex">
                  <ChevronRight className="h-4 w-4 text-slate-300" />
                </div>

              </Link>
            ))}

          {!loading && filtered.length === 0 && (
            <p className="px-5 py-10 text-center text-sm text-slate-400">
              No inspections match your filters
            </p>
          )}

        </div>
      </div>
    </div>
  );
}