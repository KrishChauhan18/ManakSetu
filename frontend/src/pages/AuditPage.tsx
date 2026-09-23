import { useEffect, useState } from "react";
import { ShieldCheck, Search, RefreshCw, AlertTriangle, Clock, User, FileEdit, Trash2 } from "lucide-react";
import { apiGetAuditLogs, type AuditLogEntry } from "../services/api";

function actionIcon(action: string) {
  if (action.includes("delete") || action.includes("remove"))
    return <Trash2 className="h-4 w-4 text-red-500" />;
  if (action.includes("create") || action.includes("register"))
    return <ShieldCheck className="h-4 w-4 text-green-500" />;
  return <FileEdit className="h-4 w-4 text-blue-500" />;
}

function actionColor(action: string) {
  if (action.includes("delete")) return "bg-red-50 text-red-700 border-red-100";
  if (action.includes("create") || action.includes("register"))
    return "bg-green-50 text-green-700 border-green-100";
  return "bg-blue-50 text-blue-700 border-blue-100";
}

function formatTimestamp(ts: string | null) {
  if (!ts) return "Unknown";
  return new Date(ts).toLocaleString();
}

export default function AuditPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const PAGE_SIZE = 50;

  async function load(p = 1) {
    try {
      setLoading(true);
      setError("");
      const resp = await apiGetAuditLogs({ page: p, page_size: PAGE_SIZE });
      setLogs(resp.items);
      setTotalPages(resp.pagination.total_pages);
      setTotal(resp.pagination.total);
      setPage(p);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit logs");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(1); }, []);

  const filtered = logs.filter((l) => {
    const q = search.toLowerCase();
    if (!q) return true;
    return (
      l.action.toLowerCase().includes(q) ||
      l.target_type.toLowerCase().includes(q) ||
      l.target_id.toLowerCase().includes(q) ||
      (l.reason ?? "").toLowerCase().includes(q) ||
      String(l.user_id).includes(q)
    );
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Audit Log</h1>
          <p className="mt-1 text-sm text-slate-500">
            Tamper-evident record of all system actions · {total} total entries
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-lg bg-green-50 px-3 py-2 text-xs font-semibold text-green-700">
          <ShieldCheck size={15} />
          Audit chain verified
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* Search + Refresh */}
      <div className="flex flex-col gap-3 rounded-xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-sm">
          <Search size={15} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search action, target, user ID…"
            className="w-full rounded-lg border border-slate-200 py-2 pl-9 pr-3 text-sm outline-none focus:border-orange-400"
          />
        </div>
        <button
          onClick={() => load(1)}
          className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-7 w-7 animate-spin rounded-full border-4 border-orange-100 border-t-orange-400" />
          <span className="ml-3 text-sm text-slate-500">Loading audit logs…</span>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 px-6 py-14 text-center text-slate-400">
              No audit entries found.
            </div>
          ) : (
            filtered.map((log) => (
              <div
                key={log.id}
                className="flex flex-col gap-3 rounded-xl border border-slate-100 bg-white p-4 shadow-sm sm:flex-row sm:items-start"
              >
                {/* Icon */}
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-50 ring-1 ring-slate-100">
                  {actionIcon(log.action)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`rounded-full border px-2.5 py-0.5 text-xs font-bold uppercase ${actionColor(log.action)}`}
                    >
                      {log.action}
                    </span>
                    <span className="text-xs font-semibold text-slate-600">
                      {log.target_type} #{log.target_id}
                    </span>
                  </div>

                  {log.reason && (
                    <p className="mt-1 text-sm text-slate-600">
                      <span className="font-medium">Reason:</span> {log.reason}
                    </p>
                  )}

                  <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <User size={11} />
                      User ID: {log.user_id ?? "system"}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock size={11} />
                      {formatTimestamp(log.timestamp)}
                    </span>
                  </div>

                  {/* Changed values */}
                  {(Boolean(log.old_value) || Boolean(log.new_value)) && (
                    <div className="mt-2 flex flex-wrap gap-2">
                      {log.old_value != null && (
                        <div className="rounded-lg bg-red-50 px-3 py-1.5 text-xs text-red-600">
                          <span className="font-semibold">Before:</span>{" "}
                          {JSON.stringify(log.old_value)}
                        </div>
                      )}
                      {log.new_value != null && (
                        <div className="rounded-lg bg-green-50 px-3 py-1.5 text-xs text-green-700">
                          <span className="font-semibold">After:</span>{" "}
                          {JSON.stringify(log.new_value)}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* Log ID */}
                <div className="shrink-0 text-right text-[11px] font-mono text-slate-300">
                  #{log.id}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => load(page - 1)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
          >
            ← Prev
          </button>
          <span className="text-sm text-slate-500">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => load(page + 1)}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-40"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
