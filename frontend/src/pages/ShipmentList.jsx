import { useEffect, useState } from "react";
import api from "@/lib/api";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Download, RefreshCw } from "lucide-react";
import { getStatusClass } from "@/lib/status";

export const ShipmentList = () => {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");
  const [exporting, setExporting] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    fetchShipments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const fetchShipments = async () => {
    try {
      const url = filter === "all" ? "/shipments" : `/shipments?status=${filter}`;
      const response = await api.get(url);
      setShipments(response.data);
    } catch (error) {
      console.error("Failed to fetch shipments", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      const res = await api.post("/shipments/refresh");
      await fetchShipments();
      toast.success(res.data?.message || "Statuses refreshed");
    } catch (error) {
      toast.error("Failed to refresh statuses");
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      const url = filter === "all"
        ? "/shipments/bulk/download"
        : `/shipments/bulk/download?status=${filter}`;
      const response = await api.get(url, { responseType: "blob" });
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

  return (
    <div className="p-4 lg:p-8" data-testid="shipments-list-page">
      <div className="mb-6 lg:mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h1 className="text-2xl lg:text-4xl font-bold tracking-tight mb-2" data-testid="shipments-title">All Shipments</h1>
          <p className="text-sm lg:text-base text-zinc-500">View and manage all your shipments</p>
        </div>
        <div className="flex gap-2 lg:gap-3 items-center flex-wrap">
          <Button
            onClick={handleRefresh}
            disabled={isRefreshing}
            data-testid="refresh-statuses-btn"
            className="bg-zinc-100 text-zinc-900 hover:bg-zinc-200 border border-zinc-200 rounded-sm whitespace-nowrap"
          >
            <RefreshCw className={`w-4 h-4 mr-1 lg:mr-2 ${isRefreshing ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">{isRefreshing ? "Refreshing..." : "Refresh"}</span>
            <span className="sm:hidden">Sync</span>
          </Button>
          <Button
            onClick={handleExport}
            disabled={exporting || shipments.length === 0}
            data-testid="export-shipments-btn"
            className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm whitespace-nowrap"
          >
            <Download className="w-4 h-4 mr-1 lg:mr-2" />
            <span className="hidden sm:inline">{exporting ? "Exporting..." : "Export CSV"}</span>
            <span className="sm:hidden">CSV</span>
          </Button>
          <div className="flex-1 sm:w-64 sm:flex-initial">
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
                <th className="px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Order ID</th>
                <th className="hidden sm:table-cell px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Waybill</th>
                <th className="hidden md:table-cell px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Type</th>
                <th className="px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Receiver</th>
                <th className="hidden lg:table-cell px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">City</th>
                <th className="px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Status</th>
                <th className="hidden lg:table-cell px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Payment</th>
                <th className="hidden xl:table-cell px-3 lg:px-6 py-3 lg:py-4 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Created</th>
              </tr>
            </thead>
            <tbody>
              {shipments.map((shipment) => (
                <tr key={shipment.id} className="border-b border-zinc-200 hover:bg-zinc-50" data-testid={`shipment-list-row-${shipment.id}`}>
                  <td className="px-3 lg:px-6 py-3 lg:py-4">
                    <Link to={`/shipments/${shipment.id}`} className="mono font-medium text-zinc-900 hover:text-red-600 text-sm" data-testid={`shipment-link-${shipment.order_id}`}>
                      {shipment.order_id}
                    </Link>
                  </td>
                  <td className="hidden sm:table-cell px-3 lg:px-6 py-3 lg:py-4 mono text-zinc-600 text-xs">{shipment.waybill || "N/A"}</td>
                  <td className="hidden md:table-cell px-3 lg:px-6 py-3 lg:py-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium border ${
                      shipment.shipment_type === "RVP"
                        ? "bg-zinc-100 text-zinc-900 border-zinc-300"
                        : "bg-white text-zinc-600 border-zinc-200"
                    }`} data-testid={`shipment-type-badge-${shipment.shipment_type}`}>
                      {shipment.shipment_type === "RVP" ? "Reverse" : "Forward"}
                    </span>
                  </td>
                  <td className="px-3 lg:px-6 py-3 lg:py-4 text-zinc-900 text-sm">{shipment.receiver.name}</td>
                  <td className="hidden lg:table-cell px-3 lg:px-6 py-3 lg:py-4 text-zinc-600">{shipment.receiver.city}</td>
                  <td className="px-3 lg:px-6 py-3 lg:py-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium border ${getStatusClass(shipment.status)}`} data-testid={`status-badge-${shipment.status}`}>
                      {shipment.status}
                    </span>
                  </td>
                  <td className="hidden lg:table-cell px-3 lg:px-6 py-3 lg:py-4 text-zinc-600">{shipment.payment_mode}</td>
                  <td className="hidden xl:table-cell px-3 lg:px-6 py-3 lg:py-4 text-zinc-600">{new Date(shipment.created_at).toLocaleDateString()}</td>
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