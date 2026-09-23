import { createContext, useContext, useState, type ReactNode } from "react";
import type { Notification, Role } from "../types";
import { INITIAL_NOTIFICATIONS } from "../data/mockData";

interface NotificationContextType {
  notifications: Notification[];
  forRole: (role: Role) => Notification[];
  unreadCount: (role: Role) => number;
  markAllRead: (role: Role) => void;
  pushRuleUpdate: (ruleId: string, ruleName: string) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

export function NotificationProvider({ children }: { children: ReactNode }) {
  const [notifications, setNotifications] = useState<Notification[]>(INITIAL_NOTIFICATIONS);

  function forRole(role: Role) {
    return notifications
      .filter((n) => n.targetRole === "All" || n.targetRole === role)
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  function unreadCount(role: Role) {
    return forRole(role).filter((n) => !n.read).length;
  }

  function markAllRead(role: Role) {
    setNotifications((prev) =>
      prev.map((n) => (n.targetRole === "All" || n.targetRole === role ? { ...n, read: true } : n))
    );
  }

  function pushRuleUpdate(ruleId: string, ruleName: string) {
    const notif: Notification = {
      id: `NOTIF-${Date.now()}`,
      type: "rule_update",
      message: `Rule ${ruleId} "${ruleName}" was updated by Administrator.`,
      relatedRuleId: ruleId,
      read: false,
      timestamp: new Date().toISOString(),
      targetRole: "Inspector",
    };
    setNotifications((prev) => [notif, ...prev]);
  }

  return (
    <NotificationContext.Provider
      value={{ notifications, forRole, unreadCount, markAllRead, pushRuleUpdate }}
    >
      {children}
    </NotificationContext.Provider>
  );
}

export function useNotifications() {
  const ctx = useContext(NotificationContext);
  if (!ctx) throw new Error("useNotifications must be used within NotificationProvider");
  return ctx;
}