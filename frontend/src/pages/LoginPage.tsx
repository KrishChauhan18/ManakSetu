import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Mail, Lock, Eye, EyeOff, ArrowRight } from "lucide-react";
import bgEmblem from "../assets/bg.jpg";
import { useAuth } from "../hooks/useAuth";
import type { Role } from "../types";
const ROLE_OPTIONS: { role: Role; title: string }[] = [
  { role: "Inspector", title: "Inspector" },
  { role: "Supervisor", title: "Supervisor" },
  { role: "Administrator", title: "Administrator" },
];

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState<Role | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin() {
    if (!selectedRole) {
      setError("Please select your role.");
      return;
    }

    if (!email || !password) {
      setError("Please enter your email and password.");
      return;
    }

    try {
      setLoading(true);
      setError("");

      await login(email, password, selectedRole);

      navigate("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Login failed. Please check your credentials."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#FCF6EA] px-4 py-10">
      {/* Ashoka emblem watermark */}
      <div className="pointer-events-none absolute right-6 top-1/2 hidden -translate-y-1/2 flex-col items-center opacity-[0.07] lg:flex">
        <img
          src={bgEmblem}
          alt=""
          className="w-[220px] object-contain"
        />
      </div>

      {/* Tricolor flowing wave (bottom-left) */}
      <svg
        className="pointer-events-none absolute bottom-0 left-0 w-full"
        height="260"
        viewBox="0 0 1536 260"
        preserveAspectRatio="none"
      >
        <path
          d="M0 160 C 300 60, 600 220, 1000 120 C 1200 70, 1400 140, 1536 90 L 1536 260 L 0 260 Z"
          fill="#F5A94D"
          opacity="0.55"
        />
        <path
          d="M0 190 C 320 100, 620 240, 980 160 C 1180 115, 1380 175, 1536 130 L 1536 260 L 0 260 Z"
          fill="#F2F2F2"
          opacity="0.55"
        />
        <path
          d="M0 220 C 340 150, 640 260, 1000 200 C 1200 165, 1380 205, 1536 175 L 1536 260 L 0 260 Z"
          fill="#3E9142"
          opacity="0.5"
        />
      </svg>

      {/* Main */}
      <div className="relative z-10 mx-auto flex max-w-[560px] flex-col items-center">
        {/* Page header */}
        <div className="mb-6 text-center">
          <h1 className="text-4xl font-bold tracking-tight text-[#0B3B6F]">
            Manak Setu
          </h1>
          <p className="mt-1 text-base text-[#5C7A9D]">
            Legal Metrology Compliance Portal
          </p>
          <div className="mt-4 flex items-center justify-center gap-2">
            <span className="h-[3px] w-24 rounded-full bg-[#E08B1D]" />
            <span className="h-[3px] w-10 rounded-full bg-[#E7E3D8]" />
            <span className="h-[3px] w-24 rounded-full bg-[#2E8B44]" />
          </div>
        </div>

        {/* Card */}
        <div className="w-full rounded-2xl border border-[#F0E4C8] bg-white p-8 shadow-[0_25px_60px_rgba(11,59,111,0.10)]">
          <div className="mb-6 text-center">
  <h1 className="text-4xl font-bold tracking-tight text-[#0B3B6F]">
    Manak Setu
  </h1>

  <p className="mt-1 text-base text-[#5C7A9D]">
    Legal Metrology Compliance Portal
  </p>

  <div className="mt-4 flex items-center justify-center gap-2">
    <span className="h-[3px] w-24 rounded-full bg-[#E08B1D]" />
    <span className="h-[3px] w-10 rounded-full bg-[#E7E3D8]" />
    <span className="h-[3px] w-24 rounded-full bg-[#2E8B44]" />
  </div>
</div>

          {/* Email */}
          <div className="mb-4">
            <div className="relative">
              <Mail className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#0B3B6F]" />
              <input
                type="email"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setError("");
                }}
                placeholder="Email Address"
                className="h-14 w-full rounded-xl border border-[#EADFC1] bg-white pl-12 pr-4 text-sm text-[#0B3B6F] outline-none transition placeholder:text-[#8B9BB0] focus:border-[#E08B1D] focus:ring-2 focus:ring-[#E08B1D]/15"
              />
            </div>
          </div>

          {/* Password */}
          <div className="mb-4">
            <div className="relative">
              <Lock className="pointer-events-none absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-[#0B3B6F]" />
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError("");
                }}
                placeholder="Password"
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleLogin();
                }}
                className="h-14 w-full rounded-xl border border-[#EADFC1] bg-white pl-12 pr-11 text-sm text-[#0B3B6F] outline-none transition placeholder:text-[#8B9BB0] focus:border-[#E08B1D] focus:ring-2 focus:ring-[#E08B1D]/15"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-[#0B3B6F] hover:text-[#E08B1D]"
              >
                {showPassword ? (
                  <EyeOff className="h-5 w-5" />
                ) : (
                  <Eye className="h-5 w-5" />
                )}
              </button>
            </div>
          </div>

          {/* Role selection */}
          <div className="mb-5">
            <label className="mb-3 block text-sm font-semibold text-[#0B3B6F]">
              Select your role
            </label>
            <div className="space-y-2">
              {ROLE_OPTIONS.map((option) => {
                const isSelected = selectedRole === option.role;
                return (
                  <label
                    key={option.role}
                    className={`flex cursor-pointer items-center gap-3 rounded-xl border px-4 py-3 transition ${
                      isSelected
                        ? "border-[#E08B1D] bg-[#FBEBD3]"
                        : "border-[#EADFC1] bg-white hover:bg-[#FBF6EA]"
                    }`}
                  >
                    <input
                      type="radio"
                      name="role"
                      value={option.role}
                      checked={isSelected}
                      onChange={() => {
                        setSelectedRole(option.role);
                        setError("");
                      }}
                      className="h-4 w-4 accent-[#E08B1D]"
                    />
                    <span
                      className={`text-sm ${
                        isSelected ? "font-medium text-[#0B3B6F]" : "text-[#0B3B6F]"
                      }`}
                    >
                      {option.title}
                    </span>
                  </label>
                );
              })}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2.5 text-xs text-red-600">
              {error}
            </div>
          )}

          {/* Login */}
          <button
            type="button"
            onClick={handleLogin}
            disabled={loading}
            className="flex h-14 w-full items-center justify-center gap-2 rounded-xl bg-[#E08B1D] text-base font-semibold text-white shadow-[0_10px_25px_rgba(224,139,29,0.30)] transition-all hover:bg-[#C87914] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              "Signing in..."
            ) : (
              <>
                Login
                <ArrowRight className="h-4 w-4" />
              </>
            )}
          </button>

          {/* Quick Demo Credentials */}
          <div className="mt-6 rounded-xl border border-slate-100 bg-slate-50/80 p-3.5">
            <p className="text-center text-xs font-semibold text-slate-500 mb-2">
              Quick Demo Logins:
            </p>
            <div className="grid grid-cols-3 gap-2">
              {[
                { role: "Inspector" as Role, email: "inspector@manaksetu.gov.in", pass: "Inspector@123" },
                { role: "Supervisor" as Role, email: "supervisor@manaksetu.gov.in", pass: "Supervisor@123" },
                { role: "Administrator" as Role, email: "admin@manaksetu.gov.in", pass: "Admin@123" },
              ].map((acc) => (
                <button
                  key={acc.role}
                  type="button"
                  onClick={() => {
                    setSelectedRole(acc.role);
                    setEmail(acc.email);
                    setPassword(acc.pass);
                    setError("");
                  }}
                  className="rounded-lg border border-slate-200 bg-white py-1.5 px-2 text-center text-xs font-medium text-slate-700 hover:border-orange-300 hover:bg-orange-50/50 transition-colors"
                >
                  {acc.role}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}