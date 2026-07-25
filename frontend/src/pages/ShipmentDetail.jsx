import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import api from "@/lib/api";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Download, RefreshCw, Package, ArrowLeft, Share2 } from "lucide-react";
import { getStatusClass } from "@/lib/status";

export const ShipmentDetail = () => {
  const { id } = useParams();
  const [shipment, setShipment] = useState(null);
  const [tracking, setTracking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [trackingLoading, setTrackingLoading] = useState(false);

  useEffect(() => {
    fetchShipment();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const fetchShipment = async () => {
    try {
      const response = await api.get(`/shipments/${id}`);
      setShipment(response.data);
      if (response.data.tracking_data) {
        setTracking(response.data.tracking_data);
      }
    } catch (error) {
      console.error("Failed to fetch shipment", error);
      toast.error("Failed to load shipment details");
    } finally {
      setLoading(false);
    }
  };

  const handleTrack = async () => {
    if (!shipment?.waybill) {
      toast.error("No waybill available to track");
      return;
    }

    setTrackingLoading(true);
    try {
      const response = await api.get(`/shipments/${id}/track`);
      setTracking(response.data);
      toast.success("Tracking information updated");
    } catch (error) {
      console.error("Failed to track shipment", error);
      toast.error("Failed to fetch tracking information");
    } finally {
      setTrackingLoading(false);
    }
  };

  const handleShareTracking = async () => {
    if (!shipment?.waybill) {
      toast.error("No waybill available");
      return;
    }
    const trackingUrl = `${window.location.origin}/track/${shipment.waybill}`;
    
    // Use Web Share API on mobile if available
    if (navigator.share) {
      try {
        await navigator.share({
          title: `Track Order ${shipment.order_id}`,
          text: `Track your shipment from ${shipment.sender.name}`,
          url: trackingUrl,
        });
        return;
      } catch (e) { /* user cancelled */ }
    }
    
    // Fallback: copy to clipboard
    try {
      await navigator.clipboard.writeText(trackingUrl);
      toast.success("Tracking link copied to clipboard!");
    } catch (e) {
      toast.error("Could not copy link");
    }
  };

  const handleDownloadLabel = async () => {
    if (!shipment?.waybill) {
      toast.error("No waybill available");
      return;
    }

    try {
      const response = await api.get(`/shipments/${id}/label`, {
        responseType: "blob",
      });
      
      // Check if it's a PDF
      const contentType = response.headers["content-type"] || "";
      if (contentType.includes("pdf")) {
        const blob = new Blob([response.data], { type: "application/pdf" });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `label_${shipment.waybill}.pdf`;
        link.click();
        window.URL.revokeObjectURL(url);
        toast.success("Label downloaded");
      } else {
        // If JSON response, try to open in new tab
        const text = await response.data.text();
        const data = JSON.parse(text);
        if (data.packages && data.packages[0]?.pdf_download_link) {
          window.open(data.packages[0].pdf_download_link, "_blank");
          toast.success("Opening label");
        } else {
          toast.error("Label format not supported. Check Delhivery portal.");
        }
      }
    } catch (error) {
      console.error("Failed to get label", error);
      toast.error(error.response?.data?.detail || "Failed to generate shipping label");
    }
  };

  if (loading) {
    return (
      <div className="p-4 lg:p-8" data-testid="shipment-detail-loading">
        <div className="text-zinc-500">Loading shipment details...</div>
      </div>
    );
  }

  if (!shipment) {
    return (
      <div className="p-4 lg:p-8" data-testid="shipment-not-found">
        <div className="text-zinc-500">Shipment not found</div>
      </div>
    );
  }

  return (
    <div className="p-4 lg:p-8" data-testid="shipment-detail-page">
      <div className="mb-8">
        <Link to="/shipments" className="inline-flex items-center gap-2 text-sm text-zinc-600 hover:text-zinc-900 mb-4" data-testid="back-to-shipments">
          <ArrowLeft className="w-4 h-4" />
          Back to Shipments
        </Link>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <div>
            <h1 className="text-2xl lg:text-4xl font-bold tracking-tight mb-2" data-testid="shipment-detail-title">
              Order <span className="mono">{shipment.order_id}</span>
            </h1>
            <p className="text-sm lg:text-base text-zinc-500">Shipment details and tracking information</p>
          </div>
          <div className="flex gap-2 lg:gap-3 flex-wrap">
            <Button
              onClick={handleTrack}
              disabled={trackingLoading || !shipment.waybill}
              data-testid="track-shipment-btn"
              className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm flex-1 sm:flex-initial"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {trackingLoading ? "Tracking..." : "Track"}
            </Button>
            <Button
              onClick={handleShareTracking}
              disabled={!shipment.waybill}
              data-testid="share-tracking-btn"
              className="bg-white border border-zinc-300 text-zinc-900 hover:bg-zinc-50 rounded-sm flex-1 sm:flex-initial"
            >
              <Share2 className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Share with Customer</span>
              <span className="sm:hidden">Share</span>
            </Button>
            <Button
              onClick={handleDownloadLabel}
              disabled={!shipment.waybill}
              data-testid="download-label-btn"
              className="bg-red-600 text-white hover:bg-red-700 rounded-sm flex-1 sm:flex-initial"
            >
              <Download className="w-4 h-4 mr-2" />
              <span className="hidden sm:inline">Download Label</span>
              <span className="sm:hidden">Label</span>
            </Button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Shipment Info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Status */}
          <div className="border border-zinc-200 rounded-sm bg-white p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-500 mb-2">Status</p>
                <span className={`inline-flex items-center px-4 py-2 rounded-sm text-sm font-medium border ${getStatusClass(shipment.status)}`} data-testid="shipment-status-badge">
                  {shipment.status}
                </span>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-zinc-500 mb-2">Waybill</p>
                <p className="mono text-lg font-bold" data-testid="shipment-waybill">{shipment.waybill || "Not assigned"}</p>
              </div>
            </div>
          </div>

          {/* Addresses */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="border border-zinc-200 rounded-sm bg-white p-6">
              <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-4">Sender</h3>
              <div className="space-y-2">
                <p className="font-medium text-zinc-900">{shipment.sender?.name}</p>
                <p className="text-sm text-zinc-600">{shipment.sender?.phone}</p>
                <p className="text-sm text-zinc-600">{shipment.sender?.address}</p>
                <p className="text-sm text-zinc-600">{shipment.sender?.city}, {shipment.sender?.state} {shipment.sender?.pincode}</p>
              </div>
            </div>

            <div className="border border-zinc-200 rounded-sm bg-white p-6">
              <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-4">Receiver</h3>
              <div className="space-y-2">
                <p className="font-medium text-zinc-900">{shipment.receiver?.name}</p>
                <p className="text-sm text-zinc-600">{shipment.receiver?.phone}</p>
                <p className="text-sm text-zinc-600">{shipment.receiver?.address}</p>
                <p className="text-sm text-zinc-600">{shipment.receiver?.city}, {shipment.receiver?.state} {shipment.receiver?.pincode}</p>
              </div>
            </div>
          </div>

          {/* Package Info */}
          <div className="border border-zinc-200 rounded-sm bg-white p-6">
            <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-4">Package Details</h3>
            <div className="space-y-3">
              {(shipment.items || []).map((item, idx) => (
                <div key={idx} className="flex justify-between items-center pb-3 border-b border-zinc-200 last:border-b-0">
                  <div>
                    <p className="font-medium text-zinc-900">{item.name}</p>
                    <p className="text-sm text-zinc-500">Qty: {item.qty}</p>
                  </div>
                  <p className="font-medium">₹{item.price}</p>
                </div>
              ))}
              <div className="grid grid-cols-2 gap-4 pt-3">
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Weight</p>
                  <p className="font-medium">{Math.round(shipment.weight * 1000)} g</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Dimensions (L×B×H)</p>
                  <p className="font-medium">{shipment.length} × {shipment.breadth} × {shipment.height} cm</p>
                </div>
                <div>
                  <p className="text-xs text-zinc-500 mb-1">Payment Mode</p>
                  <p className="font-medium">{shipment.payment_mode}</p>
                </div>
                {shipment.payment_mode === "COD" && (
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">COD Amount</p>
                    <p className="font-medium">₹{shipment.cod_amount}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Tracking Timeline */}
        <div className="lg:col-span-1">
          <div className="border border-zinc-200 rounded-sm bg-white p-6" data-testid="tracking-section">
            <h3 className="text-xs uppercase tracking-wider text-zinc-500 mb-6">Tracking Timeline</h3>
            {tracking ? (
              <div className="space-y-4">
                <div className="text-sm text-zinc-600">Tracking data available. Check Delhivery portal for detailed timeline.</div>
              </div>
            ) : (
              <div className="text-center py-8">
                <Package className="w-12 h-12 text-zinc-300 mx-auto mb-4" />
                <p className="text-sm text-zinc-500 mb-4">No tracking data yet</p>
                {shipment.waybill && (
                  <Button
                    onClick={handleTrack}
                    disabled={trackingLoading}
                    data-testid="track-now-btn"
                    size="sm"
                    className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
                  >
                    Track Now
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ShipmentDetail;