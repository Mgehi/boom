import "@/App.css";
import { BrowserRouter, Routes, Route, useLocation, Navigate } from "react-router-dom";
import { useState, useEffect } from "react";
import axios from "axios";
import Dashboard from "@/pages/Dashboard";
import CreateShipment from "@/pages/CreateShipment";
import CreateReverseShipment from "@/pages/CreateReverseShipment";
import ShipmentList from "@/pages/ShipmentList";
import ShipmentDetail from "@/pages/ShipmentDetail";
import SchedulePickup from "@/pages/SchedulePickup";
import BulkUpload from "@/pages/BulkUpload";
import Settings from "@/pages/Settings";
import Login from "@/pages/Login";
import AuthCallback from "@/pages/AuthCallback";
import Layout from "@/components/Layout";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Send cookies with all requests
axios.defaults.withCredentials = true;

const ProtectedRoute = ({ children }) => {
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(
    location.state?.user ? true : null
  );
  const [user, setUser] = useState(location.state?.user || null);

  useEffect(() => {
    if (location.state?.user) {
      setIsAuthenticated(true);
      setUser(location.state.user);
      return;
    }
    
    const checkAuth = async () => {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          withCredentials: true,
        });
        setIsAuthenticated(true);
        setUser(response.data);
      } catch (error) {
        setIsAuthenticated(false);
      }
    };
    
    checkAuth();
  }, [location.state]);

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

  return <Layout user={user} />;
};

function AppRouter() {
  const location = useLocation();
  
  // CRITICAL: Check URL fragment for session_id synchronously during render
  // This prevents race conditions before ProtectedRoute runs
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<ProtectedRoute />}>
        <Route index element={<Dashboard />} />
        <Route path="create-shipment" element={<CreateShipment />} />
        <Route path="reverse-pickup" element={<CreateReverseShipment />} />
        <Route path="bulk-upload" element={<BulkUpload />} />
        <Route path="shipments" element={<ShipmentList />} />
        <Route path="shipments/:id" element={<ShipmentDetail />} />
        <Route path="pickup" element={<SchedulePickup />} />
        <Route path="settings" element={<Settings />} />
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
