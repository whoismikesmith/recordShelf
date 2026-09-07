import { useEffect } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { socket } from "./ws";
import { SideNav, TabNav } from "./components/Nav";
import { StatusStrip } from "./components/StatusStrip";
import { ToastProvider } from "./components/Toast";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { Icons } from "./icons";
import { BrowsePage } from "./pages/Browse";
import { ShelfPage } from "./pages/Shelf";
import { OrganizePage } from "./pages/Organize";
import { ScenesPage } from "./pages/Scenes";
import { LayoutPage } from "./pages/Layout";
import { SettingsPage } from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 10000, retry: 1, refetchOnWindowFocus: false } },
});

function Shell() {
  useEffect(() => socket.start(queryClient), []);
  return (
    <div className="app">
      <SideNav />
      <main className="app-main">
        <div className="brand-mobile"><Icons.record /> recordShelf</div>
        <StatusStrip />
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<BrowsePage />} />
            <Route path="/shelf" element={<ShelfPage />} />
            <Route path="/organize" element={<OrganizePage />} />
            <Route path="/scenes" element={<ScenesPage />} />
            <Route path="/layout" element={<LayoutPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<div className="empty">Nothing here.</div>} />
          </Routes>
        </ErrorBoundary>
      </main>
      <TabNav />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Shell />
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
