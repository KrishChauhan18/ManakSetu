import { Navigate, Outlet } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { useAuth } from "../hooks/useAuth";

export function AppLayout() {
  const { user } = useAuth();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-paper">
      <Navbar />

      <main className="px-4 py-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}