import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import { Package, MapPin, Truck, CheckCircle2, Clock, AlertCircle, Undo2 } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_ICONS = {
  "Delivered": CheckCircle2,
  "In Transit": Truck,
  "Out for Delivery": Truck,
  "Manifested": Package,
  "Pending": Clock,
  "Exception": AlertCircle,
  "RTO": AlertCircle,
};

export const PublicTracking = () => {
  const { waybill } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        const response = await axios.get(`${API}/track/${waybill}`);
        setData(response.data);
      } catch (e) {
        setError(e.response?.data?.detail || "Unable to track this shipment");
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [waybill]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white" data-testid="tracking-loading">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-2 border-zinc-900 border-t-transparent rounded-full animate-spin mb-4"></div>
          <p className="text-zinc-600 text-sm">Loading tracking info...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-white p-6" data-testid="tracking-error">
        <div className="max-w-md w-full text-center border border-zinc-200 rounded-sm bg-white p-8">
          <AlertCircle className="w-12 h-12 text-red-600 mx-auto mb-4" />
          <h1 className="text-2xl font-bold tracking-tight mb-2">Tracking Not Found</h1>
          <p className="text-zinc-500 text-sm">{error || "We couldn't find a shipment with this waybill number."}</p>
          <p className="mono text-xs text-zinc-400 mt-4">{waybill}</p>
        </div>
      </div>
    );
  }

  const Icon = STATUS_ICONS[data.current_status] || Package;
  const isDelivered = data.current_status?.toLowerCase().includes("delivered");
  const isException = data.current_status?.toLowerCase().includes("exception") || data.current_status?.toLowerCase().includes("rto");

  return (
    <div className="min-h-screen bg-[#FAFAFA]" data-testid="public-tracking-page">
      {/* Header */}
      <header className="bg-white border-b border-zinc-200">
        <div className="max-w-3xl mx-auto px-4 lg:px-6 py-4 lg:py-6">
          <div className="flex items-center gap-2">
            <Package className="w-5 h-5 text-zinc-900" />
            <h1 className="text-lg font-bold tracking-tight">Delhivery Tracking</h1>
          </div>
        </div>
      </header>

      <div className="max-w-3xl mx-auto px-4 lg:px-6 py-6 lg:py-8">
        {/* Status Hero */}
        <div className={`border rounded-sm p-6 lg:p-8 mb-6 ${
          isDelivered ? "bg-zinc-900 text-white border-zinc-900" :
          isException ? "bg-red-50 border-red-200" :
          "bg-white border-zinc-200"
        }`}>
          <div className="flex items-start gap-4">
            <div className={`flex-shrink-0 w-12 h-12 rounded-sm flex items-center justify-center ${
              isDelivered ? "bg-white/10" :
              isException ? "bg-red-100" :
              "bg-zinc-100"
            }`}>
              <Icon className={`w-6 h-6 ${
                isDelivered ? "text-white" :
                isException ? "text-red-700" :
                "text-zinc-900"
              }`} />
            </div>
            <div className="flex-1 min-w-0">
              <p className={`text-xs uppercase tracking-[0.2em] mb-1 ${isDelivered ? "text-zinc-400" : "text-zinc-500"}`}>
                Current Status
              </p>
              <h2 className="text-2xl lg:text-3xl font-bold tracking-tight mb-2" data-testid="current-status">
                {data.current_status}
              </h2>
              {data.expected_delivery && !isDelivered && (
                <p className={`text-sm ${isDelivered ? "text-zinc-300" : "text-zinc-600"}`} data-testid="expected-delivery">
                  Expected delivery: <strong>{new Date(data.expected_delivery).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</strong>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Shipment Info */}
        <div className="border border-zinc-200 rounded-sm bg-white p-4 lg:p-6 mb-6">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Waybill</p>
              <p className="mono text-sm lg:text-base font-medium text-zinc-900" data-testid="waybill-number">{data.waybill}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Order ID</p>
              <p className="mono text-sm lg:text-base font-medium text-zinc-900" data-testid="order-id">{data.order_id}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Recipient</p>
              <p className="text-sm lg:text-base font-medium text-zinc-900" data-testid="recipient-name">{data.receiver_name}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Destination</p>
              <p className="text-sm lg:text-base font-medium text-zinc-900" data-testid="destination-city">{data.receiver_city}</p>
            </div>
            {data.shipment_type === "RVP" && (
              <div className="col-span-2 mt-2 inline-flex items-center gap-2 px-3 py-2 bg-zinc-50 border border-zinc-200 rounded-sm self-start">
                <Undo2 className="w-4 h-4 text-zinc-700" />
                <span className="text-xs text-zinc-700 font-medium">Reverse Pickup</span>
              </div>
            )}
          </div>
        </div>

        {/* Timeline */}
        <div className="border border-zinc-200 rounded-sm bg-white p-4 lg:p-6">
          <h3 className="text-lg font-bold tracking-tight mb-6">Tracking History</h3>
          
          {data.scans && data.scans.length > 0 ? (
            <div className="space-y-0">
              {data.scans.map((scan, idx) => (
                <div key={idx} className="relative pl-8 pb-6 last:pb-0" data-testid={`scan-${idx}`}>
                  {/* Vertical line */}
                  {idx < data.scans.length - 1 && (
                    <div className="absolute left-[7px] top-3 bottom-0 w-px bg-zinc-200" />
                  )}
                  {/* Dot */}
                  <div className={`absolute left-0 top-1 w-4 h-4 rounded-full border-2 ${
                    idx === 0 ? "bg-zinc-900 border-zinc-900" : "bg-white border-zinc-300"
                  }`} />
                  
                  <div>
                    <p className="font-medium text-zinc-900 text-sm" data-testid={`scan-status-${idx}`}>{scan.status}</p>
                    {scan.instructions && (
                      <p className="text-xs text-zinc-600 mt-1">{scan.instructions}</p>
                    )}
                    <div className="flex items-center gap-3 mt-2 text-xs text-zinc-500">
                      {scan.location && (
                        <span className="inline-flex items-center gap-1">
                          <MapPin className="w-3 h-3" />
                          {scan.location}
                        </span>
                      )}
                      {scan.datetime && (
                        <span>{new Date(scan.datetime).toLocaleString("en-IN", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8" data-testid="no-scans">
              <Clock className="w-10 h-10 text-zinc-300 mx-auto mb-3" />
              <p className="text-sm text-zinc-500">Waiting for first scan from Delhivery</p>
              <p className="text-xs text-zinc-400 mt-1">Tracking updates will appear here once your package is picked up</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <p className="text-xs text-zinc-400 text-center mt-8">
          Live tracking powered by Delhivery
        </p>
      </div>
    </div>
  );
};

export default PublicTracking;
