import { useEffect, useState } from "react";
import axios from "axios";
import { Package, TrendingUp, Truck, AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";

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

  const statCards = [
    { label: "Today's Shipments", value: stats.today_shipments, icon: Package, color: "text-zinc-900" },
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
    <div className="p-8" data-testid="dashboard">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="dashboard-title">Dashboard</h1>
        <p className="text-zinc-500">Monitor your logistics operations</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <div
              key={idx}
              data-testid={`stat-card-${stat.label.toLowerCase().replace(/[' ]/g, "-")}`}
              className="border border-zinc-200 rounded-sm p-6 bg-white"
            >
              <div className="flex items-center justify-between mb-4">
                <Icon className={`w-5 h-5 ${stat.color}`} />
              </div>
              <div className="text-3xl font-bold tracking-tight mb-1">{stat.value}</div>
              <div className="text-sm text-zinc-500 uppercase tracking-wider">{stat.label}</div>
            </div>
          );
        })}
      </div>

      {/* Recent Shipments */}
      <div className="border border-zinc-200 rounded-sm bg-white">
        <div className="p-6 border-b border-zinc-200">
          <h2 className="text-xl font-bold tracking-tight" data-testid="recent-shipments-title">Recent Shipments</h2>
        </div>
        
        {recentShipments.length === 0 ? (
          <div className="p-12 text-center" data-testid="empty-shipments">
            <img
              src="https://static.prod-images.emergentagent.com/jobs/9f4b3913-0e32-441f-a344-b5a13d5980ad/images/d3716dc3e0b8a4a4abfbdec8bcecc73e98fa16470f0502f3a683c38902e36d0e.png"
              alt="No shipments"
              className="max-w-[200px] mx-auto mb-6 opacity-60"
            />
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
                  <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Order ID</th>
                  <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Waybill</th>
                  <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Receiver</th>
                  <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Status</th>
                  <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Created</th>
                </tr>
              </thead>
              <tbody>
                {recentShipments.map((shipment) => (
                  <tr key={shipment.id} className="border-b border-zinc-200 hover:bg-zinc-50" data-testid={`shipment-row-${shipment.id}`}>
                    <td className="px-6 py-4">
                      <Link to={`/shipments/${shipment.id}`} className="mono font-medium text-zinc-900 hover:text-red-600" data-testid={`shipment-order-id-${shipment.order_id}`}>
                        {shipment.order_id}
                      </Link>
                    </td>
                    <td className="px-6 py-4 mono text-zinc-600" data-testid={`shipment-waybill-${shipment.waybill}`}>{shipment.waybill || "N/A"}</td>
                    <td className="px-6 py-4 text-zinc-900">{shipment.receiver.name}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-3 py-1 rounded-sm text-xs font-medium border ${getStatusClass(shipment.status)}`} data-testid={`shipment-status-${shipment.status}`}>
                        {shipment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-zinc-600">{new Date(shipment.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;