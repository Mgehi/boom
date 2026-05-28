import { Outlet, Link, useLocation } from "react-router-dom";
import { Package, Plus, List, Calendar, Settings as SettingsIcon, Upload } from "lucide-react";
import { Toaster } from "@/components/ui/sonner";

export const Layout = () => {
  const location = useLocation();
  
  const isActive = (path) => {
    if (path === "/" && location.pathname === "/") return true;
    if (path !== "/" && location.pathname.startsWith(path)) return true;
    return false;
  };
  
  const navItems = [
    { path: "/", icon: Package, label: "Dashboard" },
    { path: "/create-shipment", icon: Plus, label: "Create Shipment" },
    { path: "/bulk-upload", icon: Upload, label: "Bulk Upload" },
    { path: "/shipments", icon: List, label: "Shipments" },
    { path: "/pickup", icon: Calendar, label: "Schedule Pickup" },
    { path: "/settings", icon: SettingsIcon, label: "Settings" },
  ];
  
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 bg-[#FAFAFA] border-r border-zinc-200 fixed h-full">
        <div className="p-6 border-b border-zinc-200">
          <h1 className="text-xl font-bold tracking-tight" data-testid="app-title">Delhivery Logistics</h1>
          <p className="text-sm text-zinc-500 mt-1">Automation Dashboard</p>
        </div>
        
        <nav className="p-4" data-testid="main-navigation">
          {navItems.map((item) => {
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
      </aside>
      
      {/* Main Content */}
      <main className="flex-1 ml-64">
        <Outlet />
      </main>
      
      <Toaster position="top-right" />
    </div>
  );
};

export default Layout;