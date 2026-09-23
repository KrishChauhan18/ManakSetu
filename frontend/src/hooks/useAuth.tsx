import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { Officer, Role } from "../types";
import { apiLogin } from "../services/api";

interface AuthContextType {
  user: Officer | null;
  token: string | null;
  login: (email: string, password: string, role: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const USER_STORAGE_KEY = "metriaegis_user";
const TOKEN_STORAGE_KEY = "metriaegis_token";

/** Map backend roles to frontend Role type */
function mapRole(backendRole: string): Role {
  const map: Record<string, Role> = {
    inspector: "Inspector",
    supervisor: "Supervisor",
    admin: "Administrator",
    Administrator: "Administrator",
    Supervisor: "Supervisor",
    Inspector: "Inspector",
    manufacturer: "Manufacturer",
    Manufacturer: "Manufacturer",
  };
  return map[backendRole] ?? "Inspector";
}

/** Avatar color palette based on role */
function avatarColor(role: string): string {
  const map: Record<string, string> = {
    Inspector: "#2563eb",
    Supervisor: "#7c3aed",
    Administrator: "#dc2626",
  };
  return map[role] ?? "#2563eb";
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Officer | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedUser = localStorage.getItem(USER_STORAGE_KEY);
    const storedToken = localStorage.getItem(TOKEN_STORAGE_KEY);

    if (storedUser && storedToken) {
      try {
        setUser(JSON.parse(storedUser));
        setToken(storedToken);
      } catch {
        localStorage.removeItem(USER_STORAGE_KEY);
        localStorage.removeItem(TOKEN_STORAGE_KEY);
      }
    }
  }, []);

  async function login(email: string, password: string, _role: string) {
    // Call real backend — role from UI is informational only; backend determines it
    const data = await apiLogin(email, password);

    const mappedRole = mapRole(data.role);

    const officer: Officer = {
      id: String(data.user_id),
      name: data.email.split("@")[0], // use email prefix as display name
      role: mappedRole,
      department: "Legal Metrology Division",
      region: "India",
      status: "Active",
      lastActive: new Date().toISOString(),
      avatarColor: avatarColor(mappedRole),
    };

    const accessToken = data.token || data.access_token;

    setUser(officer);
    setToken(accessToken);

    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(officer));
    localStorage.setItem(TOKEN_STORAGE_KEY, accessToken);
  }

  function logout() {
    setUser(null);
    setToken(null);
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}