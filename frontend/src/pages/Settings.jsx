import { Copy, Check } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_KEY = "e77ef181577c1ea451b6f6232c55122062441079";

export const Settings = () => {
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedWebhook, setCopiedWebhook] = useState(false);

  const webhookUrl = `${BACKEND_URL}/api/orders`;

  const copyToClipboard = (text, setCopied) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-8" data-testid="settings-page">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="settings-title">Settings</h1>
        <p className="text-zinc-500">API configuration and integration details</p>
      </div>

      <div className="max-w-4xl space-y-6">
        {/* API Key */}
        <div className="border border-zinc-200 rounded-sm bg-white p-6">
          <h2 className="text-lg font-bold tracking-tight mb-4">Delhivery API Key</h2>
          <p className="text-sm text-zinc-500 mb-4">
            This API key is used to authenticate with Delhivery services for shipment creation, tracking, and label generation.
          </p>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-[#FAFAFA] border border-zinc-200 rounded-sm p-4">
              <code className="mono text-sm text-zinc-900" data-testid="api-key-display">{API_KEY}</code>
            </div>
            <Button
              onClick={() => copyToClipboard(API_KEY, setCopiedKey)}
              data-testid="copy-api-key-btn"
              className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
            >
              {copiedKey ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Webhook Endpoint */}
        <div className="border border-zinc-200 rounded-sm bg-white p-6">
          <h2 className="text-lg font-bold tracking-tight mb-4">Webhook Endpoint</h2>
          <p className="text-sm text-zinc-500 mb-4">
            Use this endpoint to send order data from your e-commerce website. Orders posted to this endpoint will automatically be created as shipments in Delhivery.
          </p>
          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 bg-[#FAFAFA] border border-zinc-200 rounded-sm p-4">
              <code className="mono text-sm text-zinc-900 break-all" data-testid="webhook-url-display">{webhookUrl}</code>
            </div>
            <Button
              onClick={() => copyToClipboard(webhookUrl, setCopiedWebhook)}
              data-testid="copy-webhook-url-btn"
              className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
            >
              {copiedWebhook ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            </Button>
          </div>

          {/* Sample Payload */}
          <div>
            <h3 className="text-sm font-medium text-zinc-900 mb-3">Sample Request Payload</h3>
            <div className="bg-zinc-950 text-zinc-50 p-4 rounded-sm overflow-x-auto">
              <pre className="text-xs mono" data-testid="sample-payload">{`{
  "order_id": "ORD12345",
  "pickup_location": "Delhi Warehouse",
  "sender": {
    "name": "Your Business Name",
    "phone": "9876543210",
    "address": "123 Business Street",
    "city": "New Delhi",
    "state": "Delhi",
    "pincode": "110001",
    "country": "India"
  },
  "receiver": {
    "name": "Customer Name",
    "phone": "9876543211",
    "email": "customer@email.com",
    "address": "456 Customer Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001",
    "country": "India"
  },
  "items": [
    {
      "name": "Product Name",
      "qty": 1,
      "price": 999.00
    }
  ],
  "payment_mode": "Prepaid",
  "cod_amount": 0,
  "weight": 0.5,
  "length": 10,
  "breadth": 10,
  "height": 10
}`}</pre>
            </div>
          </div>
        </div>

        {/* Integration Guide */}
        <div className="border border-zinc-200 rounded-sm bg-white p-6">
          <h2 className="text-lg font-bold tracking-tight mb-4">Integration Guide</h2>
          <div className="space-y-4 text-sm text-zinc-600">
            <div>
              <h4 className="font-medium text-zinc-900 mb-2">1. Automated Order Processing</h4>
              <p>Configure your e-commerce platform to POST order data to the webhook endpoint. Each order will automatically create a shipment in Delhivery and return the waybill number.</p>
            </div>
            <div>
              <h4 className="font-medium text-zinc-900 mb-2">2. Shipment Tracking</h4>
              <p>Track shipments programmatically using <code className="mono bg-zinc-100 px-2 py-1 rounded text-xs">GET /api/shipments/:id/track</code></p>
            </div>
            <div>
              <h4 className="font-medium text-zinc-900 mb-2">3. Download Labels</h4>
              <p>Generate shipping labels using <code className="mono bg-zinc-100 px-2 py-1 rounded text-xs">GET /api/shipments/:id/label</code></p>
            </div>
            <div>
              <h4 className="font-medium text-zinc-900 mb-2">4. Schedule Pickups</h4>
              <p>Schedule pickups using <code className="mono bg-zinc-100 px-2 py-1 rounded text-xs">POST /api/pickups</code></p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;