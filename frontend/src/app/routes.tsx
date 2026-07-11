import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "@/app/layout";
import { CandidatePage } from "@/pages/CandidatePage";
import { CompaniesPage } from "@/pages/CompaniesPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { DraftPage } from "@/pages/DraftPage";
import { MatchesPage } from "@/pages/MatchesPage";
import { NewRunPage } from "@/pages/NewRunPage";
import { QueuePage } from "@/pages/QueuePage";
import { RunDetailPage } from "@/pages/RunDetailPage";
import { SettingsPage } from "@/pages/SettingsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "runs/new", element: <NewRunPage /> },
      { path: "runs/:runId", element: <RunDetailPage /> },
      { path: "candidate", element: <CandidatePage /> },
      { path: "companies", element: <CompaniesPage /> },
      { path: "matches", element: <MatchesPage /> },
      { path: "drafts", element: <DraftPage /> },
      { path: "queue", element: <QueuePage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
]);
