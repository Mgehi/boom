import { useEffect, useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ShipmentList = () => {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [exporting, setExporting] = useState(false);

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

  const handleExport = async () => {
    setExporting(true);
    try {
      const url = filter === "all" 
        ? `${API}/shipments/bulk/download`
        : `${API}/shipments/bulk/download?status=${filter}`;
      const response = await axios.get(url, { responseType: "blob" });
      const blob = new Blob([response.data], { type: "text/csv" });
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = blobUrl;
      link.download = `shipments_${new Date().toISOString().split("T")[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(blobUrl);
      toast.success("Shipments exported successfully");
    } catch (error) {
      toast.error("Failed to export shipments");
    } finally {
      setExporting(false);
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
        <div className="flex gap-3 items-center">
          <Button
            onClick={handleExport}
            disabled={exporting || shipments.length === 0}
            data-testid="export-shipments-btn"
            className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            {exporting ? "Exporting..." : "Export CSV"}
          </Button>
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
      </div>

      {loading ? (
        <div className="text-zinc-500" data-testid="shipments-loading">Loading shipments...</div>
      ) : shipments.length === 0 ? (
        <div className="border border-zinc-200 rounded-sm bg-white p-12 text-center" data-testid="empty-shipments-list">
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