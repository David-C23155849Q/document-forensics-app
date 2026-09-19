import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import "./index.css";
import { currentUser } from "./lib/api";
import AssignmentDetailPage from "./pages/AssignmentDetailPage";
import AssignmentsPage from "./pages/AssignmentsPage";
import LoginPage from "./pages/LoginPage";
import SubmissionForensicPage from "./pages/SubmissionForensicPage";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const user = currentUser();
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <RequireAuth>
              <AssignmentsPage />
            </RequireAuth>
          }
        />
        <Route
          path="/assignments/:id"
          element={
            <RequireAuth>
              <AssignmentDetailPage />
            </RequireAuth>
          }
        />
        <Route
          path="/submissions/:id"
          element={
            <RequireAuth>
              <SubmissionForensicPage />
            </RequireAuth>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
