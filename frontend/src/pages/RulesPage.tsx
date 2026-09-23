import { useEffect, useState } from "react";
import { Plus, Pencil, Eye, ListTree, RefreshCw, AlertTriangle, X } from "lucide-react";
import { useToast } from "../hooks/useToast";
import { cn } from "../utils/cn";
import {
  apiListRules,
  apiToggleRule,
  apiCreateRule,
  apiDeleteRule,
  type RuleRecord,
} from "../services/api";

function severityColor(s: string) {
  if (s === "critical") return "bg-red-100 text-red-700";
  if (s === "high") return "bg-orange-100 text-orange-700";
  if (s === "medium") return "bg-yellow-100 text-yellow-700";
  return "bg-blue-100 text-blue-700";
}

function categoryDisplay(cat: string[] | string): string {
  if (Array.isArray(cat)) return cat.join(", ");
  return cat;
}

interface CreateForm {
  rule_id_str: string;
  legal_rule_ref: string;
  source_law: string;
  field: string;
  check_type: string;
  pattern: string;
  severity: string;
  category: string;
  version: string;
}

export default function RulesPage() {
  const { push } = useToast();

  const [rules, setRules] = useState<RuleRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [toggling, setToggling] = useState<string | null>(null);

  const [showCreate, setShowCreate] = useState(false);
  const [viewRule, setViewRule] = useState<RuleRecord | null>(null);
  const [creating, setCreating] = useState(false);
  const [createForm, setCreateForm] = useState<CreateForm>({
    rule_id_str: "",
    legal_rule_ref: "Rule 6",
    source_law: "Legal Metrology 2011",
    field: "",
    check_type: "presence",
    pattern: "",
    severity: "high",
    category: "all",
    version: "2011",
  });

  async function load() {
    try {
      setLoading(true);
      setError("");
      const result = await apiListRules({ page: 1, page_size: 200 });
      const items = Array.isArray(result)
        ? result
        : (result as { items: RuleRecord[] }).items ?? [];
      setRules(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load rules");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function toggle(rule: RuleRecord) {
    try {
      setToggling(rule.rule_id_str);
      const updated = await apiToggleRule(rule.rule_id_str, !rule.enabled);
      setRules((prev) =>
        prev.map((r) => (r.rule_id_str === rule.rule_id_str ? updated : r))
      );
      push(
        "success",
        `Rule ${updated.enabled ? "enabled" : "disabled"}`,
        `${rule.rule_id_str} · ${rule.field}`
      );
    } catch (err) {
      push("error", "Toggle failed", err instanceof Error ? err.message : "Error");
    } finally {
      setToggling(null);
    }
  }

  async function createRule() {
    if (!createForm.rule_id_str || !createForm.field) {
      push("error", "Validation", "Rule ID and Field are required.");
      return;
    }
    try {
      setCreating(true);
      const created = await apiCreateRule({
        rule_id_str: createForm.rule_id_str,
        legal_rule_ref: createForm.legal_rule_ref,
        source_law: createForm.source_law,
        field: createForm.field,
        check_type: createForm.check_type,
        pattern: createForm.pattern || null,
        severity: createForm.severity,
        category: createForm.category === "all" ? ["all"] : [createForm.category],
        version: createForm.version,
        enabled: true,
      });
      setRules((prev) => [created, ...prev]);
      setShowCreate(false);
      setCreateForm({
        rule_id_str: "",
        legal_rule_ref: "Rule 6",
        source_law: "Legal Metrology 2011",
        field: "",
        check_type: "presence",
        pattern: "",
        severity: "high",
        category: "all",
        version: "2011",
      });
      push("success", "Rule created", created.rule_id_str);
    } catch (err) {
      push("error", "Create failed", err instanceof Error ? err.message : "Error");
    } finally {
      setCreating(false);
    }
  }

  async function deleteRule(rule: RuleRecord) {
    if (!confirm(`Delete rule ${rule.rule_id_str}?`)) return;
    try {
      await apiDeleteRule(rule.rule_id_str);
      setRules((prev) => prev.filter((r) => r.rule_id_str !== rule.rule_id_str));
      push("success", "Rule deleted", rule.rule_id_str);
    } catch (err) {
      push("error", "Delete failed", err instanceof Error ? err.message : "Error");
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Compliance Rule Engine</h1>
          <p className="mt-1 text-sm text-slate-500">
            {rules.length} Legal Metrology rules ·{" "}
            {rules.filter((r) => r.enabled).length} active
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={load}
            className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-600 hover:bg-slate-50"
          >
            <RefreshCw size={14} /> Refresh
          </button>
          <button
            onClick={() => setShowCreate(true)}
            className="flex items-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white hover:bg-slate-700"
          >
            <Plus size={16} /> Create Custom Rule
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm text-red-700">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* Create Form */}
      {showCreate && (
        <div className="rounded-xl border border-orange-200 bg-orange-50 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-semibold text-slate-800">Create Custom Rule</h2>
            <button onClick={() => setShowCreate(false)} className="text-slate-400 hover:text-slate-700">
              <X size={16} />
            </button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <input
              placeholder="Rule ID (e.g. LM-FOOD-99)"
              value={createForm.rule_id_str}
              onChange={(e) => setCreateForm((f) => ({ ...f, rule_id_str: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
            <input
              placeholder="Field (e.g. net_weight)"
              value={createForm.field}
              onChange={(e) => setCreateForm((f) => ({ ...f, field: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
            <input
              placeholder="Legal Rule Ref (e.g. Rule 6)"
              value={createForm.legal_rule_ref}
              onChange={(e) => setCreateForm((f) => ({ ...f, legal_rule_ref: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
            <input
              placeholder="Pattern (optional regex)"
              value={createForm.pattern}
              onChange={(e) => setCreateForm((f) => ({ ...f, pattern: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
            <select
              value={createForm.severity}
              onChange={(e) => setCreateForm((f) => ({ ...f, severity: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={createForm.check_type}
              onChange={(e) => setCreateForm((f) => ({ ...f, check_type: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            >
              <option value="presence">Presence</option>
              <option value="regex">Regex</option>
              <option value="range">Range</option>
              <option value="non_empty">Non-Empty</option>
            </select>
          </div>
          <div className="mt-3 flex gap-2">
            <button
              onClick={createRule}
              disabled={creating}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60"
            >
              {creating ? "Creating…" : "Create Rule"}
            </button>
            <button
              onClick={() => setShowCreate(false)}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:bg-white"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* View Modal */}
      {viewRule && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="font-bold text-slate-900">{viewRule.rule_id_str}</h2>
              <button onClick={() => setViewRule(null)} className="text-slate-400 hover:text-slate-700">
                <X size={18} />
              </button>
            </div>
            <dl className="grid grid-cols-2 gap-3 text-sm">
              {[
                ["Field", viewRule.field],
                ["Check Type", viewRule.check_type],
                ["Severity", viewRule.severity],
                ["Source Law", viewRule.source_law],
                ["Legal Ref", viewRule.legal_rule_ref],
                ["Category", categoryDisplay(viewRule.category)],
                ["Version", viewRule.version],
                ["Status", viewRule.enabled ? "Enabled" : "Disabled"],
                ["Pattern", viewRule.pattern ?? "—"],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{k}</dt>
                  <dd className="mt-0.5 font-medium text-slate-800">{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        </div>
      )}

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-7 w-7 animate-spin rounded-full border-4 border-orange-100 border-t-orange-400" />
          <span className="ml-3 text-sm text-slate-500">Loading rules…</span>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[820px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                <th className="px-5 py-3 font-semibold">Rule ID</th>
                <th className="px-5 py-3 font-semibold">Field</th>
                <th className="px-5 py-3 font-semibold">Source Law</th>
                <th className="px-5 py-3 font-semibold">Severity</th>
                <th className="px-5 py-3 font-semibold">Category</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rules.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-5 py-10 text-center text-slate-400">
                    No rules found.
                  </td>
                </tr>
              ) : (
                rules.map((r) => (
                  <tr key={r.rule_id_str} className="border-b border-slate-50 hover:bg-slate-50/60">
                    <td className="px-5 py-3 font-mono text-xs font-medium text-slate-800">
                      <div className="flex items-center gap-1.5">
                        <ListTree size={12} className="text-slate-400" />
                        {r.rule_id_str}
                      </div>
                    </td>
                    <td className="px-5 py-3 text-slate-700">{r.field}</td>
                    <td className="px-5 py-3 text-slate-500 text-xs">{r.source_law}</td>
                    <td className="px-5 py-3">
                      <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${severityColor(r.severity)}`}>
                        {r.severity}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-500 text-xs">
                      {categoryDisplay(r.category)}
                    </td>
                    <td className="px-5 py-3">
                      <button
                        disabled={toggling === r.rule_id_str}
                        onClick={() => toggle(r)}
                        className={cn(
                          "relative h-5 w-9 rounded-full transition-colors disabled:opacity-50",
                          r.enabled ? "bg-green-500" : "bg-slate-200"
                        )}
                      >
                        <span
                          className={cn(
                            "absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform",
                            r.enabled ? "translate-x-4" : "translate-x-0"
                          )}
                        />
                      </button>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => setViewRule(r)}
                          title="View"
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <Eye size={15} />
                        </button>
                        <button
                          onClick={() => deleteRule(r)}
                          title="Delete"
                          className="rounded-md p-1.5 text-red-400 hover:bg-red-50"
                        >
                          <Pencil size={15} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
