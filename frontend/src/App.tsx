import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./hooks/useAuth";
import { ToastProvider } from "./hooks/useToast";
import { NotificationProvider } from "./hooks/useNotifications";
import { InspectionFlowProvider } from "./hooks/useInspectionFlow";
import { AppLayout } from "./layouts/AppLayout";
import { RoleGuard } from "./components/RoleGuard";

import LoginPage from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import ScanPage from "./pages/ScanPage";
import OCRResultsPage from "./pages/OCRResultsPage";
import CompliancePage from "./pages/CompliancePage";
import VerificationPage from "./pages/VerificationPage";
import ReportPage from "./pages/ReportPage";
import HistoryPage from "./pages/HistoryPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import UsersPage from "./pages/UsersPage";
import RulesPage from "./pages/RulesPage";
import AuditPage from "./pages/AuditPage";
import InspectionDetailPage from "./pages/InspectionDetailPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <AuthProvider>
      <NotificationProvider>
        <ToastProvider>
          <InspectionFlowProvider>
            <BrowserRouter>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/" element={<AppLayout />}>
                  <Route index element={<Navigate to="/login" replace />} />
                  <Route path="dashboard" element={<DashboardPage />} />
                  <Route path="scan" element={<ScanPage />} />
                  <Route path="ocr" element={<OCRResultsPage />} />
                  <Route path="verify" element={<VerificationPage />} />
                  <Route path="report/:scanId" element={<ReportPage />} />
                  <Route path="history" element={<HistoryPage />} />
                  <Route path="analytics" element={<AnalyticsPage />} />
                  <Route path="inspection/:scanId" element={<InspectionDetailPage />} />
                  <Route path="settings" element={<SettingsPage />} />

                  <Route
                    path="rules"
                    element={
                      <RoleGuard allowed={["Supervisor", "Administrator"]}>
                        <RulesPage />
                      </RoleGuard>
                    }
                  />
                  <Route
                    path="compliance"
                    element={
                      <RoleGuard allowed={["Supervisor", "Administrator"]}>
                        <CompliancePage />
                      </RoleGuard>
                    }
                  />
                  <Route
                    path="users"
                    element={
                      <RoleGuard allowed={["Supervisor", "Administrator"]}>
                        <UsersPage />
                      </RoleGuard>
                    }
                  />
                  <Route
                    path="audit"
                    element={
                      <RoleGuard allowed={["Administrator"]}>
                        <AuditPage />
                      </RoleGuard>
                    }
                  />
                </Route>
                <Route path="*" element={<Navigate to="/login" replace />} />
              </Routes>
            </BrowserRouter>
          </InspectionFlowProvider>
        </ToastProvider>
      </NotificationProvider>
    </AuthProvider>
  );
}