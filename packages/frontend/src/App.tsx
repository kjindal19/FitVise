import { useState } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { useAuth } from "./lib/auth";
import BottomNav from "./components/BottomNav";
import LogMenu from "./components/LogMenu";

import Home from "./screens/Home";
import Workout from "./screens/Workout";
import Diet from "./screens/Diet";
import Metrics from "./screens/Metrics";
import Progress from "./screens/Progress";
import Programme from "./screens/Programme";
import Journal from "./screens/Journal";
import Checkins from "./screens/Checkins";
import Settings from "./screens/Settings";
import Connect from "./screens/Connect";
import NotificationsScreen from "./screens/Notifications";
import Login from "./screens/Login";

const NAV_ROUTES = ["/", "/programme", "/progress", "/journal"];

export default function App() {
  const { loading, isMultiUser, user } = useAuth();
  const [logOpen, setLogOpen] = useState(false);
  const { pathname } = useLocation();
  const showNav = NAV_ROUTES.includes(pathname);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center font-mono text-sm text-ink3">
        Loading FitVise…
      </div>
    );
  }

  // multi_user mode requires a logged-in user for the app shell.
  if (isMultiUser && !user && pathname !== "/connect") {
    return <Login />;
  }

  // Onboarding is strictly enforced: until it is completed on the backend,
  // the user is confined to the Connect screen (the in-app onboarding surface).
  if (user && !user.onboarding_completed_at && pathname !== "/connect") {
    return <Navigate to="/connect" replace />;
  }

  return (
    <div className="relative mx-auto flex h-full max-w-[440px] flex-col overflow-hidden bg-bg">
      <main className="sa flex-1 overflow-y-auto" style={{ paddingBottom: showNav ? 80 : 0 }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/workout" element={<Workout />} />
          <Route path="/diet" element={<Diet />} />
          <Route path="/metrics" element={<Metrics />} />
          <Route path="/progress" element={<Progress />} />
          <Route path="/programme" element={<Programme />} />
          <Route path="/journal" element={<Journal />} />
          <Route path="/checkins" element={<Checkins />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/connect" element={<Connect />} />
          <Route path="/notifications" element={<NotificationsScreen />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>

      {showNav && <BottomNav onLog={() => setLogOpen(true)} />}
      {logOpen && <LogMenu onClose={() => setLogOpen(false)} />}
    </div>
  );
}
