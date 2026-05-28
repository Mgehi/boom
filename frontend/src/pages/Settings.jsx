import { useEffect, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Copy, Check, Save, Building } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const API_KEY = "e77ef181577c1ea451b6f6232c55122062441079";

export const Settings = () => {
  const [copiedKey, setCopiedKey] = useState(false);
  const [copiedWebhook, setCopiedWebhook] = useState(false);
  const [saving, setSaving] = useState(false);
  const [registering, setRegistering] = useState(false);
  const [settings, setSettings] = useState({
    business_name: "",
    sender_name: "",
    sender_phone: "",
    sender_email: "",
    sender_address: "",
    sender_city: "",
    sender_state: "",
    sender_pincode: "",
    pickup_location: "",
    seller_gst: "",
  });

  const webhookUrl = `${BACKEND_URL}/api/orders`;

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`);
      setSettings({
        business_name: response.data.business_name || "",
        sender_name: response.data.sender_name || "",
        sender_phone: response.data.sender_phone || "",
        sender_email: response.data.sender_email || "",
        sender_address: response.data.sender_address || "",
        sender_city: response.data.sender_city || "",
        sender_state: response.data.sender_state || "",
        sender_pincode: response.data.sender_pincode || "",
        pickup_location: response.data.pickup_location || "",
        seller_gst: response.data.seller_gst || "",
      });
    } catch (error) {
      console.error("Failed to load settings", error);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await axios.put(`${API}/settings`, settings);
      toast.success("Settings saved successfully");
    } catch (error) {
      toast.error("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleRegisterWarehouse = async () => {
    if (!settings.pickup_location || !settings.sender_address || !settings.sender_pincode) {
      toast.error("Please fill in pickup location, address, and pincode first, then save settings");
      return;
    }

    setRegistering(true);
    try {
      const response = await axios.post(`${API}/warehouse/register`, {
        name: settings.pickup_location,
        email: settings.sender_email || "support@business.com",
        phone: settings.sender_phone,
        address: settings.sender_address,
        city: settings.sender_city,
        state: settings.sender_state,
        country: "India",
        pin: settings.sender_pincode,
      });
      toast.success(response.data?.message || "Warehouse registered successfully with Delhivery");
    } catch (error) {
      const errorMsg = error.response?.data?.detail || "Failed to register warehouse";
      // If warehouse already exists, that's actually OK
      if (errorMsg.toLowerCase().includes("already") || errorMsg.toLowerCase().includes("exist")) {
        toast.info("This warehouse is already registered with Delhivery");
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setRegistering(false);
    }
  };

  const copyToClipboard = (text, setCopied) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="p-8" data-testid="settings-page">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="settings-title">Settings</h1>
        <p className="text-zinc-500">Configure your business details and view API integration</p>
      </div>

      <div className="max-w-4xl space-y-6">
        {/* Default Sender Details */}
        <form onSubmit={handleSave} className="border border-zinc-200 rounded-sm bg-white p-6">
          <div className="flex items-center gap-2 mb-2">
            <Building className="w-5 h-5 text-zinc-700" />
            <h2 className="text-lg font-bold tracking-tight">Default Sender / Business Details</h2>
          </div>
          <p className="text-sm text-zinc-500 mb-6">
            Configure your business address once. It will be used as the sender for all shipments.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Business Name</Label>
              <Input
                name="business_name"
                value={settings.business_name}
                onChange={handleChange}
                data-testid="business-name-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Pickup Location Name *</Label>
              <Input
                name="pickup_location"
                value={settings.pickup_location}
                onChange={handleChange}
                placeholder="e.g., Mumbai_Warehouse"
                required
                data-testid="pickup-location-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
              <p className="text-xs text-zinc-500 mt-1">Must match your registered Delhivery warehouse</p>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender Name *</Label>
              <Input
                name="sender_name"
                value={settings.sender_name}
                onChange={handleChange}
                required
                data-testid="sender-name-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender Phone *</Label>
              <Input
                name="sender_phone"
                value={settings.sender_phone}
                onChange={handleChange}
                required
                data-testid="sender-phone-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender Email</Label>
              <Input
                name="sender_email"
                type="email"
                value={settings.sender_email}
                onChange={handleChange}
                data-testid="sender-email-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender Pincode *</Label>
              <Input
                name="sender_pincode"
                value={settings.sender_pincode}
                onChange={handleChange}
                required
                data-testid="sender-pincode-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div className="md:col-span-2">
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender Address *</Label>
              <Input
                name="sender_address"
                value={settings.sender_address}
                onChange={handleChange}
                required
                data-testid="sender-address-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender City *</Label>
              <Input
                name="sender_city"
                value={settings.sender_city}
                onChange={handleChange}
                required
                data-testid="sender-city-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Sender State *</Label>
              <Input
                name="sender_state"
                value={settings.sender_state}
                onChange={handleChange}
                required
                data-testid="sender-state-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
            </div>
            <div className="md:col-span-2">
              <Label className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Seller GSTIN (Optional)</Label>
              <Input
                name="seller_gst"
                value={settings.seller_gst}
                onChange={handleChange}
                placeholder="e.g., 27ABCDE1234F1Z5"
                data-testid="seller-gst-setting-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono"
              />
              <p className="text-xs text-zinc-500 mt-1">Your business GST number. Will be auto-filled on all shipments and invoices.</p>
            </div>
          </div>

          <div className="mt-6 flex flex-col gap-3">
            <div className="bg-zinc-50 border border-zinc-200 p-3 rounded-sm text-xs text-zinc-600">
              <strong className="text-zinc-900">Important:</strong> Before creating shipments, register your pickup warehouse with Delhivery. Save your settings first, then click "Register Warehouse with Delhivery". The warehouse name above must match exactly when creating shipments.
            </div>
            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={saving}
                data-testid="save-settings-btn"
                className="bg-red-600 text-white hover:bg-red-700 rounded-sm"
              >
                <Save className="w-4 h-4 mr-2" />
                {saving ? "Saving..." : "Save Settings"}
              </Button>
              <Button
                type="button"
                onClick={handleRegisterWarehouse}
                disabled={registering}
                data-testid="register-warehouse-btn"
                className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
              >
                {registering ? "Registering..." : "Register Warehouse with Delhivery"}
              </Button>
            </div>
          </div>
        </form>

        {/* API Key */}
        <div className="border border-zinc-200 rounded-sm bg-white p-6">
          <h2 className="text-lg font-bold tracking-tight mb-4">Delhivery API Key</h2>
          <p className="text-sm text-zinc-500 mb-4">Used to authenticate with Delhivery services.</p>
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
            POST orders from your e-commerce website to this URL for automatic shipment creation.
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

          <div>
            <h3 className="text-sm font-medium text-zinc-900 mb-3">Sample Payload</h3>
            <div className="bg-zinc-950 text-zinc-50 p-4 rounded-sm overflow-x-auto">
              <pre className="text-xs mono">{`{
  "order_id": "ORD12345",
  "pickup_location": "${settings.pickup_location || "Your_Warehouse"}",
  "sender": { /* Your business details */ },
  "receiver": {
    "name": "Customer Name",
    "phone": "9876543211",
    "address": "456 Customer Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
  },
  "items": [{ "name": "Product", "qty": 1, "price": 999 }],
  "payment_mode": "Prepaid",
  "weight": 0.5
}`}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
