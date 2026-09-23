import { Navigate } from "react-router-dom";
import type { ReactNode } from "react";
import type { Role } from "../types";
import { useAuth } from "../hooks/useAuth";

export function RoleGuard({ allowed, children }: { allowed: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!allowed.includes(user.role)) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}