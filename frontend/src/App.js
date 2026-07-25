import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import api from "@/lib/api";
import Dashboard from "@/pages/Dashboard";
import CreateShipment from "@/pages/CreateShipment";
import CreateReverseShipment from "@/pages/CreateReverseShipment";
import ShipmentList from "@/pages/ShipmentList";
import ShipmentDetail from "@/pages/ShipmentDetail";
import SchedulePickup from "@/pages/SchedulePickup";
import BulkUpload from "@/pages/BulkUpload";
import Settings from "@/pages/Settings";
import Admin from "@/pages/Admin";
import Login from "@/pages/Login";
import PublicTracking from "@/pages/PublicTracking";
import Layout from "@/components/Layout";
import { SettingsProvider } from "@/contexts/SettingsContext";

const ProtectedRoute = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [user, setUser] = useState(null);

  useEffect(() => {
    api.get("/auth/me")
      .then((response) => {
        setIsAuthenticated(true);
        setUser(response.data);
      })
      .catch(() => setIsAuthenticated(false));
  }, []);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white" data-testid="auth-loading">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-zinc-600 text-sm">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <SettingsProvider>
      <Layout user={user} />
    </SettingsProvider>
  );
};

function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/track/:waybill" element={<PublicTracking />} />
      <Route path="/" element={<ProtectedRoute />}>
        <Route index element={<Dashboard />} />
        <Route path="create-shipment" element={<CreateShipment />} />
        <Route path="reverse-pickup" element={<CreateReverseShipment />} />
        <Route path="bulk-upload" element={<BulkUpload />} />
        <Route path="shipments" element={<ShipmentList />} />
        <Route path="shipments/:id" element={<ShipmentDetail />} />
        <Route path="pickup" element={<SchedulePickup />} />
        <Route path="settings" element={<Settings />} />
        <Route path="admin" element={<Admin />} />
      </Route>
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </div>
  );
}

export default App;
