import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ShipmentList = () => {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchShipments();
  }, [filter]);

  const fetchShipments = async () => {
    try {
      const url = filter === "all" ? `${API}/shipments` : `${API}/shipments?status=${filter}`;
      const response = await axios.get(url);
      setShipments(response.data);
    } catch (error) {
      console.error("Failed to fetch shipments", error);
    } finally {
      setLoading(false);
    }
  };

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

  return (
    <div className="p-8" data-testid="shipments-list-page">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="shipments-title">All Shipments</h1>
          <p className="text-zinc-500">View and manage all your shipments</p>
        </div>
        <div className="w-64">
          <Select value={filter} onValueChange={setFilter}>
            <SelectTrigger data-testid="status-filter-select" className="bg-white border-zinc-200 rounded-sm">
              <SelectValue placeholder="Filter by status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Shipments</SelectItem>
              <SelectItem value="Pending">Pending</SelectItem>
              <SelectItem value="Manifested">Manifested</SelectItem>
              <SelectItem value="In Transit">In Transit</SelectItem>
              <SelectItem value="Delivered">Delivered</SelectItem>
              <SelectItem value="Exception">Exception</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="text-zinc-500" data-testid="shipments-loading">Loading shipments...</div>
      ) : shipments.length === 0 ? (
        <div className="border border-zinc-200 rounded-sm bg-white p-12 text-center" data-testid="empty-shipments-list">
          <img
            src="https://static.prod-images.emergentagent.com/jobs/9f4b3913-0e32-441f-a344-b5a13d5980ad/images/d3716dc3e0b8a4a4abfbdec8bcecc73e98fa16470f0502f3a683c38902e36d0e.png"
            alt="No shipments"
            className="max-w-[200px] mx-auto mb-6 opacity-60"
          />
          <p className="text-zinc-500 mb-4">No shipments found</p>
          <Link
            to="/create-shipment"
            data-testid="create-shipment-cta"
            className="inline-flex items-center gap-2 bg-red-600 text-white px-6 py-3 rounded-sm font-medium hover:bg-red-700 transition-colors"
          >
            Create Shipment
          </Link>
        </div>
      ) : (
        <div className="border border-zinc-200 rounded-sm bg-white overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-[#FAFAFA]">
              <tr className="border-b border-zinc-200">
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Order ID</th>
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Waybill</th>
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Receiver</th>
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">City</th>
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Status</th>
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Payment</th>
                <th className="px-6 py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Created</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map((shipment) => (
                <tr key={shipment.id} className="border-b border-zinc-200 hover:bg-zinc-50" data-testid={`shipment-list-row-${shipment.id}`}>
                  <td className="px-6 py-4">
                    <Link to={`/shipments/${shipment.id}`} className="mono font-medium text-zinc-900 hover:text-red-600" data-testid={`shipment-link-${shipment.order_id}`}>
                      {shipment.order_id}
                    </Link>
                  </td>
                  <td className="px-6 py-4 mono text-zinc-600">{shipment.waybill || "N/A"}</td>
                  <td className="px-6 py-4 text-zinc-900">{shipment.receiver.name}</td>
                  <td className="px-6 py-4 text-zinc-600">{shipment.receiver.city}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center px-3 py-1 rounded-sm text-xs font-medium border ${getStatusClass(shipment.status)}`} data-testid={`status-badge-${shipment.status}`}>
                      {shipment.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-zinc-600">{shipment.payment_mode}</td>
                  <td className="px-6 py-4 text-zinc-600">{new Date(shipment.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default ShipmentList;