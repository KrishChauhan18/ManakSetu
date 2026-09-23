import { useState } from "react";
import { NavLink } from "react-router-dom";
import { Bell, ChevronDown } from "lucide-react";
import { useAuth } from "../hooks/useAuth";
import { useNotifications } from "../hooks/useNotifications";


type NavItem = {
  label: string;
  path: string;
};

export function Navbar() {
  const { user } = useAuth();
  const { forRole, unreadCount, markAllRead } = useNotifications();

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  if (!user) return null;

  const role = user.role;

  /*
   * ROLE BASED NAVIGATION
   *
   * Inspector:
   * Dashboard | New Scan | History | Analytics
   *
   * Supervisor:
   * Dashboard | History | Analytics | Rules | Users
   *
   * Administrator:
   * Dashboard | History | Analytics | Rules | Compliance | Users | Audit Trail
   */

  const items: NavItem[] = [
    { label: "Dashboard", path: "/dashboard" },
    { label: "History", path: "/history" },
    { label: "Analytics", path: "/analytics" },
  ];

  // Inspector only
  if (role === "Inspector") {
    items.splice(1, 0, {
      label: "New Scan",
      path: "/scan",
    });
  }

  // Supervisor
  if (role === "Supervisor") {
    items.push(
      { label: "Rules", path: "/rules" },
      { label: "Users", path: "/users" }
    );
  }

  // Administrator
  if (role === "Administrator") {
    items.push(
      { label: "Rules", path: "/rules" },
      { label: "Compliance", path: "/compliance" },
      { label: "Users", path: "/users" },
      { label: "Audit Trail", path: "/audit" }
    );
  }

  const notifications = forRole(user.role);
  const unread = unreadCount(user.role);

  const handleNotificationClick = () => {
    setNotificationsOpen((value) => !value);

    if (!notificationsOpen) {
      markAllRead(user.role);
    }
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b border-orange-200 bg-white shadow-sm">

      {/* ================= MAIN NAVBAR ================= */}
      <div className="flex h-[82px] w-full items-center px-8 xl:px-14 2xl:px-20">
    {/* ================= LOGO ================= */}
<NavLink
  to="/dashboard"
  className="flex w-[310px] shrink-0 items-center"
>
  <div className="flex items-center">

    {/* Tricolor accent */}
    <div className="mr-3 h-11 w-1.5 rounded-full bg-gradient-to-b from-orange-400 via-white to-green-500 shadow-sm" />

    <div>
      <div className="text-[23px] font-bold leading-5 tracking-tight text-[#153b6b]">
        Manak Setu
      </div>

      <div className="mt-2 text-[11px] font-medium leading-3 text-slate-500">
        Legal Metrology Inspector Portal
      </div>
    </div>

  </div>
</NavLink>

        {/* ================= NAVIGATION ================= */}
        <nav className="hidden flex-1 items-center justify-center gap-2 lg:flex">

          {items.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `
                whitespace-nowrap
                rounded-xl
                px-6
                py-3
                text-sm
                font-semibold
                transition-all
                duration-200
                ${
                  isActive
                    ? "bg-[#f5a623] text-white shadow-sm"
                    : "text-[#173b68] hover:bg-orange-50 hover:text-[#d98200]"
                }
                `
              }
            >
              {item.label}
            </NavLink>
          ))}

        </nav>

        {/* ================= RIGHT SIDE ================= */}
        <div className="ml-auto flex min-w-[260px] shrink-0 items-center justify-end gap-5">

          {/* ================= NOTIFICATIONS ================= */}
          <div className="relative">

            <button
              onClick={handleNotificationClick}
              className="
                relative
                rounded-xl
                p-3
                text-[#173b68]
                transition
                hover:bg-orange-50
              "
            >
              <Bell className="h-5 w-5" />

              {unread > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[9px] font-bold text-white">
                  {unread}
                </span>
              )}
            </button>

            {notificationsOpen && (
              <div className="absolute right-0 mt-3 w-80 overflow-hidden rounded-xl border border-orange-100 bg-white shadow-xl">

                <div className="border-b border-orange-100 px-5 py-4">
                  <p className="text-sm font-semibold text-[#173b68]">
                    Notifications
                  </p>
                </div>

                <div className="max-h-80 overflow-y-auto">

                  {notifications.length === 0 ? (
                    <p className="px-5 py-10 text-center text-sm text-slate-400">
                      No notifications
                    </p>
                  ) : (
                    notifications.map((notification) => (
                      <div
                        key={notification.id}
                        className="border-b border-orange-50 px-5 py-4 last:border-0"
                      >
                        <p className="text-sm text-slate-700">
                          {notification.message}
                        </p>

                        <p className="mt-1 text-xs text-slate-400">
                          {new Date(
                            notification.timestamp
                          ).toLocaleString()}
                        </p>
                      </div>
                    ))
                  )}

                </div>
              </div>
            )}

          </div>

          {/* ================= PROFILE ================= */}
          <div className="relative">

            <button
              onClick={() => setProfileOpen((value) => !value)}
              className="
                flex
                items-center
                gap-3
                rounded-xl
                px-2
                py-2
                transition
                hover:bg-orange-50
              "
            >

              {/* Avatar */}
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-[#173b68] text-sm font-bold text-white shadow-sm">
                {user.name?.charAt(0).toUpperCase()}
              </div>

              {/* User information */}
              <div className="hidden text-left md:block">

                <p className="text-sm font-semibold leading-4 text-[#173b68]">
                  {user.name}
                </p>

                <p className="mt-1 text-[11px] font-medium text-slate-500">
                  {user.role}
                </p>

              </div>

              <ChevronDown className="hidden h-4 w-4 text-slate-500 md:block" />

            </button>

            {/* PROFILE DROPDOWN */}
            {profileOpen && (
              <div className="absolute right-0 mt-3 w-56 rounded-xl border border-orange-100 bg-white p-2 shadow-xl">

                <div className="border-b border-orange-100 px-4 py-3">

                  <p className="text-sm font-semibold text-[#173b68]">
                    {user.name}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {user.role}
                  </p>

                </div>

                <button
                  onClick={() => {
                    localStorage.removeItem("token");
                    window.location.href = "/login";
                  }}
                  className="
                    mt-1
                    w-full
                    rounded-lg
                    px-4
                    py-2.5
                    text-left
                    text-sm
                    font-medium
                    text-red-600
                    transition
                    hover:bg-red-50
                  "
                >
                  Log out
                </button>

              </div>
            )}

          </div>

        </div>

      </div>

      {/* ================= MOBILE NAVIGATION ================= */}
      <div className="flex gap-1 overflow-x-auto border-t border-orange-100 bg-orange-50/40 px-5 py-2.5 lg:hidden">

        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `
              whitespace-nowrap
              rounded-lg
              px-4
              py-2
              text-xs
              font-semibold
              ${
                isActive
                  ? "bg-[#f5a623] text-white"
                  : "text-[#173b68] hover:bg-orange-100"
              }
              `
            }
          >
            {item.label}
          </NavLink>
        ))}

      </div>

    </header>
  );
}