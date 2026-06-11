import { Outlet, Link, useLocation, useNavigate } from "react-router-dom";
import { useState, useEffect } from "react";
import { Package, Plus, List, Calendar, Settings as SettingsIcon, Upload, Undo2, LogOut, Menu, X, Shield } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Layout = ({ user }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  
  // Close mobile drawer on route change
  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);
  
  const isActive = (path) => {
    if (path === "/" && location.pathname === "/") return true;
    if (path !== "/" && location.pathname.startsWith(path)) return true;
    return false;
  };
  
  const isCreateActive = location.pathname === "/create-shipment" || location.pathname === "/reverse-pickup";
  
  const navItems = [
    { path: "/", icon: Package, label: "Dashboard" },
    { path: "/shipments", icon: List, label: "Shipments" },
    { path: "/bulk-upload", icon: Upload, label: "Bulk Upload" },
    { path: "/pickup", icon: Calendar, label: "Schedule Pickup" },
    { path: "/settings", icon: SettingsIcon, label: "Settings" },
    ...(user?.is_admin ? [{ path: "/admin", icon: Shield, label: "Admin" }] : []),
  ];
  
  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
    } catch (e) { /* ignore */ }
    navigate("/login");
    window.location.reload();
  };
  
  const SidebarContent = () => (
    <>
      <div className="p-6 border-b border-zinc-200 flex items-center justify-between">
        <div>
          <h1 className="text-lg lg:text-xl font-bold tracking-tight" data-testid="app-title">Delhivery Logistics</h1>
          <p className="text-xs lg:text-sm text-zinc-500 mt-1">Automation Dashboard</p>
        </div>
        {/* Close button on mobile */}
        <button
          onClick={() => setMobileOpen(false)}
          className="lg:hidden p-2 -mr-2 text-zinc-600 hover:text-zinc-900"
          data-testid="mobile-close-btn"
          aria-label="Close menu"
        >
          <X className="w-5 h-5" />
        </button>
      </div>
      
      <nav className="p-4 flex-1 overflow-y-auto" data-testid="main-navigation">
        {/* Dashboard */}
        <Link
          to="/"
          data-testid="nav-dashboard"
          className={`flex items-center gap-3 px-4 py-3 mb-1 text-sm font-medium transition-colors rounded-sm ${
            isActive("/") && location.pathname === "/"
              ? "bg-zinc-900 text-white"
              : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
          }`}
        >
          <Package className="w-4 h-4" />
          Dashboard
        </Link>
        
        {/* Create Shipment with Sub-items */}
        <div className="mb-1">
          <div
            data-testid="nav-create-shipment-parent"
            className={`flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-sm ${
              isCreateActive ? "bg-zinc-100 text-zinc-900" : "text-zinc-600"
            }`}
          >
            <Plus className="w-4 h-4" />
            Create Shipment
          </div>
          <div className="ml-4 pl-3 border-l border-zinc-200 mt-1">
            <Link
              to="/create-shipment"
              data-testid="nav-forward-shipment"
              className={`flex items-center gap-3 px-3 py-2 mb-1 text-sm transition-colors rounded-sm ${
                location.pathname === "/create-shipment"
                  ? "bg-zinc-900 text-white font-medium"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
              }`}
            >
              <Plus className="w-3 h-3" />
              Forward Shipment
            </Link>
            <Link
              to="/reverse-pickup"
              data-testid="nav-reverse-pickup"
              className={`flex items-center gap-3 px-3 py-2 mb-1 text-sm transition-colors rounded-sm ${
                location.pathname === "/reverse-pickup"
                  ? "bg-zinc-900 text-white font-medium"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
              }`}
            >
              <Undo2 className="w-3 h-3" />
              Reverse Pickup
            </Link>
          </div>
        </div>
        
        {/* Other items */}
        {navItems.slice(1).map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          
          return (
            <Link
              key={item.path}
              to={item.path}
              data-testid={`nav-${item.label.toLowerCase().replace(" ", "-")}`}
              className={`flex items-center gap-3 px-4 py-3 mb-1 text-sm font-medium transition-colors rounded-sm ${
                active
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-600 hover:bg-zinc-100 hover:text-zinc-900"
              }`}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      
      {/* User profile & logout */}
      {user && (
        <div className="border-t border-zinc-200 p-4" data-testid="user-section">
          <div className="flex items-center gap-3 mb-3">
            {user.picture ? (
              <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full border border-zinc-200" />
            ) : (
              <div className="w-8 h-8 rounded-full bg-zinc-900 text-white flex items-center justify-center text-sm font-bold">
                {(user.name || user.email || "?").charAt(0).toUpperCase()}
              </div>
            )}
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-zinc-900 truncate" data-testid="user-name">{user.name || user.email}</p>
              <p className="text-xs text-zinc-500 truncate" data-testid="user-email">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            data-testid="logout-btn"
            className="w-full flex items-center justify-center gap-2 text-sm text-zinc-600 hover:text-zinc-900 hover:bg-zinc-100 px-3 py-2 rounded-sm transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Sign Out
          </button>
        </div>
      )}
    </>
  );
  
  return (
    <div className="flex min-h-screen">
      {/* Mobile Top Bar */}
      <header className="lg:hidden fixed top-0 left-0 right-0 z-30 bg-white border-b border-zinc-200 flex items-center justify-between px-4 h-14">
        <button
          onClick={() => setMobileOpen(true)}
          className="p-2 -ml-2 text-zinc-700"
          data-testid="mobile-menu-btn"
          aria-label="Open menu"
        >
          <Menu className="w-6 h-6" />
        </button>
        <h1 className="text-base font-bold tracking-tight">Delhivery Logistics</h1>
        {user?.picture ? (
          <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full border border-zinc-200" />
        ) : user ? (
          <div className="w-8 h-8 rounded-full bg-zinc-900 text-white flex items-center justify-center text-sm font-bold">
            {(user.name || user.email || "?").charAt(0).toUpperCase()}
          </div>
        ) : <div className="w-8" />}
      </header>
      
      {/* Mobile drawer backdrop */}
      {mobileOpen && (
        <div
          onClick={() => setMobileOpen(false)}
          className="lg:hidden fixed inset-0 bg-zinc-900/50 z-40"
          data-testid="mobile-backdrop"
        />
      )}
      
      {/* Sidebar - mobile drawer + desktop fixed */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-72 lg:w-64 bg-[#FAFAFA] border-r border-zinc-200
          flex flex-col transition-transform duration-200 ease-out
          ${mobileOpen ? "translate-x-0" : "-translate-x-full"}
          lg:translate-x-0
        `}
        data-testid="sidebar"
      >
        <SidebarContent />
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 lg:ml-64 pt-14 lg:pt-0 min-w-0">
        <Outlet />
      </main>
      
      <Toaster position="top-right" />
    </div>
  );
};

export default Layout;
