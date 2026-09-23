import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  ScanLine,
  History,
  BarChart3,
  ShieldCheck,
  ClipboardList,
  Users,
  FileClock,
  Settings,
  X,
  ShieldAlert,
  LogOut,
  ChevronRight,
} from "lucide-react";

import { useAuth } from "../hooks/useAuth";
import type { Role } from "../types";

interface NavItem {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
  roles: Role[];
}

// DO NOT CHANGE THESE ROLE PERMISSIONS
const NAV_ITEMS: NavItem[] = [
  {
    label: "Dashboard",
    to: "/dashboard",
    icon: LayoutDashboard,
    roles: ["Inspector", "Supervisor", "Administrator"],
  },
  {
    label: "New Inspection",
    to: "/scan",
    icon: ScanLine,
    roles: ["Inspector", "Supervisor", "Administrator"],
  },
  {
    label: "History",
    to: "/history",
    icon: History,
    roles: ["Inspector", "Supervisor", "Administrator"],
  },
  {
    label: "Analytics",
    to: "/analytics",
    icon: BarChart3,
    roles: ["Inspector", "Supervisor", "Administrator"],
  },
  {
    label: "Rules",
    to: "/rules",
    icon: ClipboardList,
    roles: ["Supervisor", "Administrator"],
  },
  {
    label: "Compliance",
    to: "/compliance",
    icon: ShieldCheck,
    roles: ["Supervisor", "Administrator"],
  },
  {
    label: "Users",
    to: "/users",
    icon: Users,
    roles: ["Supervisor", "Administrator"],
  },
  {
    label: "Audit Trail",
    to: "/audit",
    icon: FileClock,
    roles: ["Administrator"],
  },
  {
    label: "Settings",
    to: "/settings",
    icon: Settings,
    roles: ["Inspector", "Supervisor", "Administrator"],
  },
];

export function Sidebar({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const { user, logout } = useAuth();

  if (!user) return null;

  // IMPORTANT: role-based sidebar remains unchanged
  const items = NAV_ITEMS.filter((item) =>
    item.roles.includes(user.role)
  );

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={`
          fixed inset-y-0 left-0 z-50
          flex w-64 flex-col
          bg-[#0B1F3A]
          text-white
          shadow-[8px_0_30px_rgba(2,20,45,0.18)]
          transition-transform duration-300
          lg:translate-x-0
          ${open ? "translate-x-0" : "-translate-x-full"}
        `}
      >
        {/* Logo */}
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-white/10 px-5">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 shadow-lg shadow-blue-900/30">
              <ShieldAlert className="h-5 w-5 text-white" />
            </div>

            <div>
              <p className="text-[15px] font-bold tracking-tight text-white">
                ManakSetu
              </p>

              <p className="text-[9px] font-semibold uppercase tracking-[0.12em] text-blue-300">
                Inspector Portal
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-blue-200 hover:bg-white/10 hover:text-white lg:hidden"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <div className="flex-1 overflow-y-auto px-3 py-5">
          <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.14em] text-blue-300/70">
            Navigation
          </p>

          <nav className="space-y-1.5">
            {items.map(({ label, to, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                onClick={onClose}
                className={({ isActive }) =>
                  `
                  group flex items-center gap-3 rounded-xl px-3 py-2.5
                  text-sm font-medium transition-all duration-200
                  ${
                    isActive
                      ? "bg-blue-600 text-white shadow-lg shadow-blue-950/20"
                      : "text-blue-100/75 hover:bg-white/10 hover:text-white"
                  }
                  `
                }
              >
                {({ isActive }) => (
                  <>
                    <div
                      className={`
                        flex h-8 w-8 shrink-0 items-center justify-center rounded-lg
                        transition-all
                        ${
                          isActive
                            ? "bg-white/15 text-white"
                            : "bg-white/5 text-blue-200 group-hover:bg-white/10 group-hover:text-white"
                        }
                      `}
                    >
                      <Icon className="h-[17px] w-[17px]" />
                    </div>

                    <span className="flex-1">{label}</span>

                    <ChevronRight
                      className={`
                        h-4 w-4 transition-all
                        ${
                          isActive
                            ? "translate-x-0 text-white opacity-100"
                            : "-translate-x-1 text-blue-300 opacity-0 group-hover:translate-x-0 group-hover:opacity-100"
                        }
                      `}
                    />
                  </>
                )}
              </NavLink>
            ))}
          </nav>
        </div>

        {/* User section */}
        <div className="shrink-0 border-t border-white/10 p-4">
          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <div className="flex items-center gap-3">
              <div
                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white shadow-md"
                style={{ backgroundColor: user.avatarColor }}
              >
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")}
              </div>

              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-white">
                  {user.name}
                </p>

                <div className="mt-0.5 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />

                  <p className="truncate text-xs text-blue-200/70">
                    {user.role}
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={logout}
              className="
                mt-3 flex w-full items-center justify-center gap-2
                rounded-lg border border-white/10
                bg-white/5 py-2
                text-xs font-semibold text-blue-100
                transition-colors
                hover:bg-red-500/15
                hover:text-red-300
              "
            >
              <LogOut className="h-3.5 w-3.5" />
              Log out
            </button>
          </div>
        </div>
      </aside>
    </>
  );
}