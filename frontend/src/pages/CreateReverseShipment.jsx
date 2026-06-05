import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Undo2, AlertCircle } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CreateReverseShipment = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [settings, setSettings] = useState(null);
  const [formData, setFormData] = useState({
    order_id: "",
    customer_name: "",
    customer_phone: "",
    customer_email: "",
    customer_address: "",
    customer_city: "",
    customer_state: "",
    customer_pincode: "",
    item_name: "",
    item_qty: 1,
    item_price: 0,
    hsn_code: "",
    payment_mode: "Prepaid",
    cod_amount: 0,
    weight_grams: 500,
    length: 10,
    breadth: 10,
    height: 10,
    seller_invoice: "",
  });

  useEffect(() => {
    axios.get(`${API}/settings`).then((res) => {
      if (res.data?.sender_name) {
        setSettings(res.data);
      }
    }).catch(() => {});
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!settings) {
      toast.error("Please configure your warehouse/sender details in Settings first");
      return;
    }
    
    setLoading(true);

    try {
      // For reverse pickup:
      // - Sender (in our API) = warehouse (from settings)
      // - Receiver (in our API) = customer (where Delhivery picks up from)
      // - shipment_type = RVP
      const payload = {
        order_id: formData.order_id,
        pickup_location: settings.pickup_location,
        sender: {
          name: settings.sender_name,
          phone: settings.sender_phone,
          email: settings.sender_email || undefined,
          address: settings.sender_address,
          city: settings.sender_city,
          state: settings.sender_state,
          pincode: settings.sender_pincode,
          country: "India",
        },
        receiver: {
          name: formData.customer_name,
          phone: formData.customer_phone,
          email: formData.customer_email || undefined,
          address: formData.customer_address,
          city: formData.customer_city,
          state: formData.customer_state,
          pincode: formData.customer_pincode,
          country: "India",
        },
        items: [
          {
            name: formData.item_name,
            qty: parseInt(formData.item_qty),
            price: parseFloat(formData.item_price),
            hsn_code: formData.hsn_code || "",
          },
        ],
        payment_mode: formData.payment_mode,
        cod_amount: formData.payment_mode === "COD" ? parseFloat(formData.cod_amount) : 0,
        weight: parseFloat(formData.weight_grams) / 1000,  // convert grams to kg for backend
        length: parseFloat(formData.length),
        breadth: parseFloat(formData.breadth),
        height: parseFloat(formData.height),
        seller_gst: settings.seller_gst || "",
        seller_invoice: formData.seller_invoice || "",
        shipment_type: "RVP",
      };

      const response = await axios.post(`${API}/shipments`, payload);
      toast.success("Reverse pickup created successfully!");
      navigate(`/shipments/${response.data.id}`);
    } catch (error) {
      console.error("Failed to create reverse pickup", error);
      toast.error(error.response?.data?.detail || "Failed to create reverse pickup");
    } finally {
      setLoading(false);
    }
  };

  if (!settings) {
    return (
      <div className="p-8" data-testid="reverse-shipment-no-settings">
        <div className="mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-2">Create Reverse Pickup</h1>
          <p className="text-zinc-500">Pick up a package from your customer back to your warehouse</p>
        </div>
        <div className="max-w-3xl border border-zinc-200 rounded-sm bg-white p-8 text-center">
          <AlertCircle className="w-12 h-12 text-zinc-400 mx-auto mb-4" />
          <h3 className="text-lg font-bold tracking-tight mb-2">Setup Required</h3>
          <p className="text-zinc-500 mb-6">
            Configure your warehouse/sender details in Settings before creating reverse pickups.
          </p>
          <Button
            onClick={() => navigate("/settings")}
            data-testid="go-to-settings-btn"
            className="bg-red-600 text-white hover:bg-red-700 rounded-sm"
          >
            Go to Settings
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8" data-testid="create-reverse-shipment-page">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Undo2 className="w-8 h-8 text-zinc-900" />
          <h1 className="text-4xl font-bold tracking-tight" data-testid="reverse-shipment-title">Create Reverse Pickup</h1>
        </div>
        <p className="text-zinc-500">Pick up a package from your customer back to your warehouse</p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-5xl">
        {/* Info banner */}
        <div className="bg-zinc-50 border-l-4 border-zinc-900 p-4 rounded-sm mb-6" data-testid="rvp-info-banner">
          <p className="text-sm text-zinc-700">
            <strong className="text-zinc-900">Reverse Pickup:</strong> Delhivery will pick up the package from the customer's address and deliver it back to your warehouse <strong className="mono">{settings.pickup_location}</strong>.
          </p>
        </div>

        <div className="border border-zinc-200 rounded-sm bg-white">
          {/* Order Details */}
          <div className="p-6 border-b border-zinc-200">
            <h2 className="text-lg font-bold tracking-tight mb-4">Order Details</h2>
            <div>
              <Label htmlFor="order_id" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Order ID / RMA Number *</Label>
              <Input
                id="order_id"
                name="order_id"
                value={formData.order_id}
                onChange={handleChange}
                required
                placeholder="e.g., RVP-2026-001 or RMA12345"
                data-testid="order-id-input"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono"
              />
            </div>
          </div>

          {/* Pickup From (Customer) */}
          <div className="p-6 border-b border-zinc-200">
            <h2 className="text-lg font-bold tracking-tight mb-1">Pickup From (Customer)</h2>
            <p className="text-sm text-zinc-500 mb-4">Where Delhivery will pick up the package</p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="customer_name" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Customer Name *</Label>
                <Input id="customer_name" name="customer_name" value={formData.customer_name} onChange={handleChange} required data-testid="customer-name-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="customer_phone" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Phone *</Label>
                <Input id="customer_phone" name="customer_phone" value={formData.customer_phone} onChange={handleChange} required data-testid="customer-phone-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="customer_email" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Email</Label>
                <Input id="customer_email" name="customer_email" type="email" value={formData.customer_email} onChange={handleChange} data-testid="customer-email-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div className="md:col-span-2">
                <Label htmlFor="customer_address" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Address *</Label>
                <Input id="customer_address" name="customer_address" value={formData.customer_address} onChange={handleChange} required data-testid="customer-address-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="customer_city" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">City *</Label>
                <Input id="customer_city" name="customer_city" value={formData.customer_city} onChange={handleChange} required data-testid="customer-city-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="customer_state" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">State *</Label>
                <Input id="customer_state" name="customer_state" value={formData.customer_state} onChange={handleChange} required data-testid="customer-state-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="customer_pincode" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Pincode *</Label>
                <Input id="customer_pincode" name="customer_pincode" value={formData.customer_pincode} onChange={handleChange} required data-testid="customer-pincode-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono" />
              </div>
            </div>
          </div>

          {/* Package Details */}
          <div className="p-6 border-b border-zinc-200">
            <h2 className="text-lg font-bold tracking-tight mb-4">Package Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="md:col-span-2">
                <Label htmlFor="item_name" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Item Name *</Label>
                <Input id="item_name" name="item_name" value={formData.item_name} onChange={handleChange} required data-testid="item-name-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="item_qty" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Quantity *</Label>
                <Input id="item_qty" name="item_qty" type="number" min="1" value={formData.item_qty} onChange={handleChange} required data-testid="item-qty-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="item_price" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Price (₹) *</Label>
                <Input id="item_price" name="item_price" type="number" step="0.01" min="0" value={formData.item_price} onChange={handleChange} required data-testid="item-price-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div>
                <Label htmlFor="hsn_code" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">HSN Code</Label>
                <Input id="hsn_code" name="hsn_code" value={formData.hsn_code} onChange={handleChange} placeholder="e.g., 6109" data-testid="hsn-code-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono" />
              </div>
              <div>
                <Label htmlFor="seller_invoice" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">RMA / Invoice Number</Label>
                <Input id="seller_invoice" name="seller_invoice" value={formData.seller_invoice} onChange={handleChange} placeholder="e.g., RMA-2026-001" data-testid="invoice-number-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono" />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
              <div>
                <Label htmlFor="weight_grams" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Weight (g) *</Label>
                <Input id="weight_grams" name="weight_grams" type="number" step="1" min="1" value={formData.weight_grams} onChange={handleChange} required data-testid="weight-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                <p className="text-xs text-zinc-500 mt-1">in grams (e.g., 500)</p>
              </div>
              <div>
                <Label htmlFor="length" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Length (cm) *</Label>
                <Input id="length" name="length" type="number" min="1" value={formData.length} onChange={handleChange} required data-testid="length-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="breadth" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Breadth (cm) *</Label>
                <Input id="breadth" name="breadth" type="number" min="1" value={formData.breadth} onChange={handleChange} required data-testid="breadth-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
              <div>
                <Label htmlFor="height" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Height (cm) *</Label>
                <Input id="height" name="height" type="number" min="1" value={formData.height} onChange={handleChange} required data-testid="height-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
              </div>
            </div>
          </div>

          {/* Payment */}
          <div className="p-6">
            <h2 className="text-lg font-bold tracking-tight mb-4">Payment</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="payment_mode" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Payment Mode *</Label>
                <Select value={formData.payment_mode} onValueChange={(value) => setFormData((prev) => ({ ...prev, payment_mode: value }))}>
                  <SelectTrigger data-testid="payment-mode-select" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Prepaid">Prepaid (no refund/charges)</SelectItem>
                    <SelectItem value="COD">COD (refund to customer)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {formData.payment_mode === "COD" && (
                <div>
                  <Label htmlFor="cod_amount" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Refund Amount (₹) *</Label>
                  <Input id="cod_amount" name="cod_amount" type="number" step="0.01" min="0" value={formData.cod_amount} onChange={handleChange} required data-testid="cod-amount-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <Button
            type="submit"
            disabled={loading}
            data-testid="create-reverse-shipment-submit-btn"
            className="bg-red-600 text-white px-8 py-3 rounded-sm font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-600 transition-colors"
          >
            {loading ? "Creating Reverse Pickup..." : "Create Reverse Pickup"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CreateReverseShipment;
