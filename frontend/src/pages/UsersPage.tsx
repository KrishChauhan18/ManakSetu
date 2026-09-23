import { useEffect, useState } from "react";
import { UserPlus, Pencil, UserX, MapPin, RefreshCw, AlertTriangle } from "lucide-react";
import { useToast } from "../hooks/useToast";
import {
  apiListUsers,
  apiCreateUser,
  apiUpdateUser,
  apiDeleteUser,
  type UserRecord,
} from "../services/api";

function roleBadgeColor(role: string) {
  if (role === "admin") return "bg-red-50 text-red-700 border-red-200";
  if (role === "supervisor") return "bg-purple-50 text-purple-700 border-purple-200";
  return "bg-blue-50 text-blue-700 border-blue-200";
}

function ActiveBadge({ active }: { active: boolean }) {
  return (
    <span
      className={`rounded-full px-2.5 py-1 text-xs font-semibold ${active ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"
        }`}
    >
      {active ? "Active" : "Inactive"}
    </span>
  );
}

interface CreateForm {
  email: string;
  password: string;
  role: string;
  region: string;
}

export default function UsersPage() {
  const { push } = useToast();

  const [users, setUsers] = useState<UserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState<CreateForm>({
    email: "",
    password: "",
    role: "inspector",
    region: "",
  });
  const [creating, setCreating] = useState(false);

  async function load() {
    try {
      setLoading(true);
      setError("");
      const result = await apiListUsers({ page: 1, page_size: 100 });
      const items = Array.isArray(result) ? result : (result as { items: UserRecord[] }).items ?? [];
      setUsers(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function toggleActive(u: UserRecord) {
    try {
      const updated = await apiUpdateUser(u.id, { is_active: !u.is_active });
      setUsers((prev) => prev.map((x) => (x.id === u.id ? updated : x)));
      push("success", `User ${updated.is_active ? "activated" : "deactivated"}`, updated.email);
    } catch (err) {
      push("error", "Update failed", err instanceof Error ? err.message : "Error");
    }
  }

  async function deleteUser(u: UserRecord) {
    if (!confirm(`Delete user ${u.email}? This cannot be undone.`)) return;
    try {
      await apiDeleteUser(u.id);
      setUsers((prev) => prev.filter((x) => x.id !== u.id));
      push("success", "User deleted", u.email);
    } catch (err) {
      push("error", "Delete failed", err instanceof Error ? err.message : "Error");
    }
  }

  async function createUser() {
    if (!createForm.email || !createForm.password) {
      push("error", "Validation", "Email and password are required.");
      return;
    }
    try {
      setCreating(true);
      const created = await apiCreateUser({
        email: createForm.email,
        password: createForm.password,
        role: createForm.role,
        region: createForm.region || undefined,
      });
      setUsers((prev) => [created, ...prev]);
      setShowCreate(false);
      setCreateForm({ email: "", password: "", role: "inspector", region: "" });
      push("success", "User created", created.email);
    } catch (err) {
      push("error", "Create failed", err instanceof Error ? err.message : "Error");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">User Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            {users.length} accounts · Inspectors, Supervisors &amp; Administrators
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
            <UserPlus size={16} /> Add User
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
          <h2 className="mb-4 font-semibold text-slate-800">Create New User</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <input
              type="email"
              placeholder="Email"
              value={createForm.email}
              onChange={(e) => setCreateForm((f) => ({ ...f, email: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
            <input
              type="password"
              placeholder="Password"
              value={createForm.password}
              onChange={(e) => setCreateForm((f) => ({ ...f, password: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
            <select
              value={createForm.role}
              onChange={(e) => setCreateForm((f) => ({ ...f, role: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            >
              <option value="inspector">Inspector</option>
              <option value="supervisor">Supervisor</option>
              <option value="admin">Administrator</option>
            </select>
            <input
              type="text"
              placeholder="Region (optional)"
              value={createForm.region}
              onChange={(e) => setCreateForm((f) => ({ ...f, region: e.target.value }))}
              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-orange-400"
            />
          </div>
          <div className="mt-3 flex gap-2">
            <button
              onClick={createUser}
              disabled={creating}
              className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-700 disabled:opacity-60"
            >
              {creating ? "Creating…" : "Create User"}
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

      {/* Table */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="h-7 w-7 animate-spin rounded-full border-4 border-orange-100 border-t-orange-400" />
          <span className="ml-3 text-sm text-slate-500">Loading users…</span>
        </div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                <th className="px-5 py-3 font-semibold">User</th>
                <th className="px-5 py-3 font-semibold">Role</th>
                <th className="px-5 py-3 font-semibold">Region</th>
                <th className="px-5 py-3 font-semibold">Status</th>
                <th className="px-5 py-3 font-semibold">Created</th>
                <th className="px-5 py-3 font-semibold">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-5 py-10 text-center text-slate-400">
                    No users found.
                  </td>
                </tr>
              ) : (
                users.map((u) => (
                  <tr key={u.id} className="border-b border-slate-50 hover:bg-slate-50/60">
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-2.5">
                        <div
                          className="flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold text-white"
                          style={{
                            background:
                              u.role === "admin"
                                ? "#dc2626"
                                : u.role === "supervisor"
                                  ? "#7c3aed"
                                  : "#2563eb",
                          }}
                        >
                          {u.email[0].toUpperCase()}
                        </div>
                        <div>
                          <p className="font-medium text-slate-800">{u.email}</p>
                          <p className="text-[11px] text-slate-400">ID #{u.id}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-5 py-3">
                      <span
                        className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${roleBadgeColor(u.role)}`}
                      >
                        {u.role}
                      </span>
                    </td>
                    <td className="px-5 py-3 text-slate-500">
                      {u.region ? (
                        <span className="flex items-center gap-1">
                          <MapPin size={12} />
                          {u.region}
                        </span>
                      ) : (
                        <span className="text-slate-300">—</span>
                      )}
                    </td>
                    <td className="px-5 py-3">
                      <ActiveBadge active={u.is_active} />
                    </td>
                    <td className="px-5 py-3 text-slate-500">
                      {u.created_at
                        ? new Date(u.created_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center gap-1">
                        <button
                          title={u.is_active ? "Deactivate" : "Activate"}
                          onClick={() => toggleActive(u)}
                          className="rounded-md p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                        >
                          <UserX size={15} />
                        </button>
                        <button
                          title="Delete user"
                          onClick={() => deleteUser(u)}
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
