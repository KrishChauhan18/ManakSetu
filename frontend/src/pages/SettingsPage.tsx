import { useState } from "react";
import { Moon, Sun, Bell, Globe, Shield } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useToast } from "../hooks/useToast";
import { cn } from "../utils/cn";

export default function SettingsPage() {
  const { user } = useAuth();
  const { push } = useToast();
  const [dark, setDark] = useState(false);
  const [notif, setNotif] = useState(true);

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-text-1">Settings</h1>
        <p className="mt-1 text-sm text-text-2">Manage your account and application preferences.</p>
      </div>

      <div className="rounded-xl border border-line bg-paper-card p-5">
        <h3 className="mb-4 font-display text-sm font-bold text-text-1">Profile</h3>
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-cyan-500 to-violet-500 text-sm font-bold text-white">
            {(user?.name ?? "AS").split(" ").map((s) => s[0]).join("")}
          </div>
          <div>
            <p className="text-sm font-semibold text-text-1">{user?.name}</p>
            <p className="text-xs text-text-3">{user?.id} · {user?.role} · {user?.region}</p>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-line bg-paper-card p-5">
        <h3 className="mb-4 font-display text-sm font-bold text-text-1">Preferences</h3>
        <div className="space-y-1">
          <ToggleRow icon={dark ? Moon : Sun} label="Dark mode" desc="Prototype visual preview only" checked={dark} onChange={() => { setDark((v) => !v); push("info", "Preview only", "Dark mode is a visual preview in this prototype."); }} />
          <ToggleRow icon={Bell} label="Push notifications" desc="Receive alerts for potential issues" checked={notif} onChange={() => setNotif((v) => !v)} />
        </div>
      </div>

      <div className="rounded-xl border border-line bg-paper-card p-5">
        <h3 className="mb-4 font-display text-sm font-bold text-text-1">Region &amp; language</h3>
        <div className="flex items-center gap-3 text-sm text-text-2">
          <Globe size={16} className="text-text-3" /> English (India) · {user?.region ?? "Dehradun"} zone
        </div>
      </div>

      <div className="flex items-center gap-2 rounded-xl border border-ok-500/30 bg-ok-50 p-4 text-xs text-ok-600">
        <Shield size={15} /> Your session is protected by role-based access control and a tamper-evident audit trail.
      </div>
    </div>
  );
}

function ToggleRow({ icon: Icon, label, desc, checked, onChange }: { icon: typeof Sun; label: string; desc: string; checked: boolean; onChange: () => void }) {
  return (
    <div className="flex items-center justify-between border-b border-line/70 py-3 last:border-0">
      <div className="flex items-center gap-3">
        <Icon size={16} className="text-text-3" />
        <div>
          <p className="text-sm font-medium text-text-1">{label}</p>
          <p className="text-xs text-text-3">{desc}</p>
        </div>
      </div>
      <button onClick={onChange} className={cn("relative h-5 w-9 rounded-full transition-colors", checked ? "bg-ok-500" : "bg-line")}>
        <span className={cn("absolute top-0.5 left-0.5 h-4 w-4 rounded-full bg-white shadow transition-transform", checked && "translate-x-4")} />
      </button>
    </div>
  );
}
