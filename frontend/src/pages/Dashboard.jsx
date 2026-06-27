import { useEffect, useState } from "react";
import axios from "axios";
import { Package, TrendingUp, Truck, AlertCircle, Plus, RefreshCw } from "lucide-react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import PincodeChecker from "@/components/PincodeChecker";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const [stats, setStats] = useState({
    total_shipments: 0,
    today_shipments: 0,
    in_transit: 0,
    delivered: 0,
    exceptions: 0,
  });
  const [recentShipments, setRecentShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, shipmentsRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/shipments?limit=10`),
      ]);
      
      setStats(statsRes.data);
      setRecentShipments(shipmentsRes.data);
    } catch (error) {
      console.error("Failed to fetch dashboard data", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setSyncing(true);
    try {
      const res = await axios.post(`${API}/shipments/refresh`);
      await fetchDashboardData();
      toast.success(res.data?.message || "Statuses refreshed");
    } catch (error) {
      toast.error("Failed to refresh statuses");
    } finally {
      setSyncing(false);
    }
  };

  const statCards = [
    { label: "Total Shipments", value: stats.total_shipments, icon: Package, color: "text-zinc-900" },
    { label: "Today's Shipments", value: stats.today_shipments, icon: Plus, color: "text-zinc-900" },
    { label: "In Transit", value: stats.in_transit, icon: Truck, color: "text-zinc-600" },
    { label: "Delivered", value: stats.delivered, icon: TrendingUp, color: "text-zinc-900" },
    { label: "Exceptions", value: stats.exceptions, icon: AlertCircle, color: "text-red-600" },
  ];

  const getStatusClass = (status) => {
    const statusMap = {
      Delivered: "bg-zinc-900 text-white border-transparent",
      "In Transit": "bg-zinc-100 text-zinc-900 border-zinc-300",
      Exception: "bg-red-50 text-red-700 border-red-200",
      Pending: "bg-white text-zinc-600 border-zinc-200",
      Manifested: "bg-zinc-100 text-zinc-900 border-zinc-300",
    };
    return statusMap[status] || "bg-white text-zinc-600 border-zinc-200";
  };

  if (loading) {
    return (
      <div className="p-8" data-testid="dashboard-loading">
        <div className="text-zinc-500">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8" data-testid="dashboard">
      <div className="mb-6 lg:mb-8 flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
        <div>
          <h1 className="text-3xl lg:text-4xl font-bold tracking-tight mb-2" data-testid="dashboard-title">Dashboard</h1>
          <p className="text-sm lg:text-base text-zinc-500">Monitor your logistics operations</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={syncing}
          data-testid="refresh-statuses-btn"
          className="inline-flex items-center gap-2 bg-zinc-900 text-white px-4 py-2 rounded-sm font-medium text-sm hover:bg-zinc-800 transition-colors disabled:opacity-60 self-start"
        >
          <RefreshCw className={`w-4 h-4 ${syncing ? "animate-spin" : ""}`} />
          {syncing ? "Refreshing..." : "Refresh Statuses"}
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 lg:gap-4 mb-6 lg:mb-8">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              data-testid={`stat-card-${stat.label.toLowerCase().replace(/[' ]/g, "-")}`}
              className="border border-zinc-200 rounded-sm p-4 lg:p-6 bg-white"
            >
              <div className="flex items-center justify-between mb-3 lg:mb-4">
                <Icon className={`w-4 h-4 lg:w-5 lg:h-5 ${stat.color}`} />
              </div>
              <div className="text-2xl lg:text-3xl font-bold tracking-tight mb-1">{stat.value}</div>
              <div className="text-xs lg:text-sm text-zinc-500 uppercase tracking-wider">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* Two column layout: Recent Shipments + Pincode Checker */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
        {/* Recent Shipments */}
        <div className="lg:col-span-2 border border-zinc-200 rounded-sm bg-white order-2 lg:order-1">
          <div className="p-4 lg:p-6 border-b border-zinc-200">
            <h2 className="text-lg lg:text-xl font-bold tracking-tight" data-testid="recent-shipments-title">Recent Shipments</h2>
          </div>
          
          {recentShipments.length === 0 ? (
            <div className="p-8 lg:p-12 text-center" data-testid="empty-shipments">
              <Package className="w-12 h-12 lg:w-16 lg:h-16 text-zinc-300 mx-auto mb-4" />
              <p className="text-zinc-500 mb-4">No shipments found</p>
              <Link
                to="/create-shipment"
                data-testid="create-first-shipment-btn"
                className="inline-flex items-center gap-2 bg-red-600 text-white px-6 py-3 rounded-sm font-medium hover:bg-red-700 transition-colors"
              >
                Create Your First Shipment
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-[#FAFAFA]">
                  <tr className="border-b border-zinc-200">
                    <th className="px-3 lg:px-4 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Order</th>
                    <th className="hidden sm:table-cell px-3 lg:px-4 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Waybill</th>
                    <th className="px-3 lg:px-4 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Receiver</th>
                    <th className="px-3 lg:px-4 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {recentShipments.map((shipment) => (
                    <tr key={shipment.id} className="border-b border-zinc-200 hover:bg-zinc-50" data-testid={`shipment-row-${shipment.id}`}>
                      <td className="px-3 lg:px-4 py-3 lg:py-4">
                        <Link to={`/shipments/${shipment.id}`} className="mono font-medium text-zinc-900 hover:text-red-600">
                          {shipment.order_id}
                        </Link>
                      </td>
                      <td className="hidden sm:table-cell px-3 lg:px-4 py-3 lg:py-4 mono text-zinc-600 text-xs">{shipment.waybill || "N/A"}</td>
                      <td className="px-3 lg:px-4 py-3 lg:py-4 text-zinc-900 text-sm">{shipment.receiver.name}</td>
                      <td className="px-3 lg:px-4 py-3 lg:py-4">
                        <span className={`inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium border ${getStatusClass(shipment.status)}`}>
                          {shipment.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Pincode Checker Widget */}
        <div className="lg:col-span-1 order-1 lg:order-2">
          <PincodeChecker />
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
