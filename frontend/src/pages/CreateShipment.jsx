import { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CreateShipment = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    order_id: "",
    pickup_location: "",
    sender_name: "",
    sender_phone: "",
    sender_email: "",
    sender_address: "",
    sender_city: "",
    sender_state: "",
    sender_pincode: "",
    receiver_name: "",
    receiver_phone: "",
    receiver_email: "",
    receiver_address: "",
    receiver_city: "",
    receiver_state: "",
    receiver_pincode: "",
    item_name: "",
    item_qty: 1,
    item_price: 0,
    hsn_code: "",
    payment_mode: "Prepaid",
    cod_amount: 0,
    weight: 0.5,
    length: 10,
    breadth: 10,
    height: 10,
    seller_gst: "",
    seller_invoice: "",
    shipment_type: "FWD",
  });

  // Auto-load default sender from settings
  useEffect(() => {
    axios.get(`${API}/settings`).then((res) => {
      const s = res.data;
      if (s?.sender_name) {
        setFormData((prev) => ({
          ...prev,
          pickup_location: s.pickup_location || "",
          sender_name: s.sender_name || "",
          sender_phone: s.sender_phone || "",
          sender_email: s.sender_email || "",
          sender_address: s.sender_address || "",
          sender_city: s.sender_city || "",
          sender_state: s.sender_state || "",
          sender_pincode: s.sender_pincode || "",
          seller_gst: s.seller_gst || "",
        }));
      }
    }).catch(() => {});
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        order_id: formData.order_id,
        pickup_location: formData.pickup_location,
        sender: {
          name: formData.sender_name,
          phone: formData.sender_phone,
          email: formData.sender_email || undefined,
          address: formData.sender_address,
          city: formData.sender_city,
          state: formData.sender_state,
          pincode: formData.sender_pincode,
          country: "India",
        },
        receiver: {
          name: formData.receiver_name,
          phone: formData.receiver_phone,
          email: formData.receiver_email || undefined,
          address: formData.receiver_address,
          city: formData.receiver_city,
          state: formData.receiver_state,
          pincode: formData.receiver_pincode,
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
        weight: parseFloat(formData.weight),
        length: parseFloat(formData.length),
        breadth: parseFloat(formData.breadth),
        height: parseFloat(formData.height),
        seller_gst: formData.seller_gst || "",
        seller_invoice: formData.seller_invoice || "",
        shipment_type: formData.shipment_type,
      };

      const response = await axios.post(`${API}/shipments`, payload);
      toast.success("Shipment created successfully!");
      navigate(`/shipments/${response.data.id}`);
    } catch (error) {
      console.error("Failed to create shipment", error);
      toast.error(error.response?.data?.detail || "Failed to create shipment");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8" data-testid="create-shipment-page">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="create-shipment-title">Create Shipment</h1>
        <p className="text-zinc-500">Fill in the details to create a new shipment</p>
      </div>

      <form onSubmit={handleSubmit} className="max-w-6xl">
        <div className="border border-zinc-200 rounded-sm bg-white">
          {/* Order Details */}
          <div className="p-6 border-b border-zinc-200">
            <h2 className="text-lg font-bold tracking-tight mb-4">Order Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label htmlFor="order_id" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Order ID *</Label>
                <Input
                  id="order_id"
                  name="order_id"
                  value={formData.order_id}
                  onChange={handleChange}
                  required
                  data-testid="order-id-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
                />
              </div>
              <div>
                <Label htmlFor="pickup_location" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Pickup Location *</Label>
                <Input
                  id="pickup_location"
                  name="pickup_location"
                  value={formData.pickup_location}
                  onChange={handleChange}
                  required
                  data-testid="pickup-location-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
                />
              </div>
              <div>
                <Label htmlFor="shipment_type" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Shipment Type *</Label>
                <Select
                  value={formData.shipment_type}
                  onValueChange={(value) => setFormData((prev) => ({ ...prev, shipment_type: value }))}
                >
                  <SelectTrigger data-testid="shipment-type-select" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="FWD">Forward (Warehouse to Customer)</SelectItem>
                    <SelectItem value="RVP">Reverse (Customer to Warehouse)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            {formData.shipment_type === "RVP" && (
              <div className="mt-3 p-3 bg-zinc-50 border-l-4 border-zinc-900 text-xs text-zinc-700 rounded-sm" data-testid="reverse-shipment-notice">
                <strong>Reverse Pickup:</strong> Sender = your warehouse, Receiver = customer to pickup from. Delhivery will pick up the package from the customer's address.
              </div>
            )}
          </div>

          {/* Sender & Receiver in 2-column layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2">
            {/* Sender Details */}
            <div className="p-6 border-b lg:border-b-0 lg:border-r border-zinc-200">
              <h2 className="text-lg font-bold tracking-tight mb-4">Sender Details</h2>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="sender_name" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Name *</Label>
                  <Input id="sender_name" name="sender_name" value={formData.sender_name} onChange={handleChange} required data-testid="sender-name-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div>
                  <Label htmlFor="sender_phone" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Phone *</Label>
                  <Input id="sender_phone" name="sender_phone" value={formData.sender_phone} onChange={handleChange} required data-testid="sender-phone-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div>
                  <Label htmlFor="sender_email" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Email</Label>
                  <Input id="sender_email" name="sender_email" type="email" value={formData.sender_email} onChange={handleChange} data-testid="sender-email-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div>
                  <Label htmlFor="sender_address" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Address *</Label>
                  <Input id="sender_address" name="sender_address" value={formData.sender_address} onChange={handleChange} required data-testid="sender-address-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="sender_city" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">City *</Label>
                    <Input id="sender_city" name="sender_city" value={formData.sender_city} onChange={handleChange} required data-testid="sender-city-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                  </div>
                  <div>
                    <Label htmlFor="sender_state" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">State *</Label>
                    <Input id="sender_state" name="sender_state" value={formData.sender_state} onChange={handleChange} required data-testid="sender-state-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                  </div>
                </div>
                <div>
                  <Label htmlFor="sender_pincode" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Pincode *</Label>
                  <Input id="sender_pincode" name="sender_pincode" value={formData.sender_pincode} onChange={handleChange} required data-testid="sender-pincode-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
              </div>
            </div>

            {/* Receiver Details */}
            <div className="p-6 border-b border-zinc-200">
              <h2 className="text-lg font-bold tracking-tight mb-4">Receiver Details</h2>
              <div className="space-y-4">
                <div>
                  <Label htmlFor="receiver_name" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Name *</Label>
                  <Input id="receiver_name" name="receiver_name" value={formData.receiver_name} onChange={handleChange} required data-testid="receiver-name-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div>
                  <Label htmlFor="receiver_phone" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Phone *</Label>
                  <Input id="receiver_phone" name="receiver_phone" value={formData.receiver_phone} onChange={handleChange} required data-testid="receiver-phone-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div>
                  <Label htmlFor="receiver_email" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Email</Label>
                  <Input id="receiver_email" name="receiver_email" type="email" value={formData.receiver_email} onChange={handleChange} data-testid="receiver-email-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div>
                  <Label htmlFor="receiver_address" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Address *</Label>
                  <Input id="receiver_address" name="receiver_address" value={formData.receiver_address} onChange={handleChange} required data-testid="receiver-address-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="receiver_city" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">City *</Label>
                    <Input id="receiver_city" name="receiver_city" value={formData.receiver_city} onChange={handleChange} required data-testid="receiver-city-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                  </div>
                  <div>
                    <Label htmlFor="receiver_state" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">State *</Label>
                    <Input id="receiver_state" name="receiver_state" value={formData.receiver_state} onChange={handleChange} required data-testid="receiver-state-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                  </div>
                </div>
                <div>
                  <Label htmlFor="receiver_pincode" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Pincode *</Label>
                  <Input id="receiver_pincode" name="receiver_pincode" value={formData.receiver_pincode} onChange={handleChange} required data-testid="receiver-pincode-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
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
                <Label htmlFor="seller_invoice" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Invoice Number</Label>
                <Input id="seller_invoice" name="seller_invoice" value={formData.seller_invoice} onChange={handleChange} placeholder="e.g., INV-2026-001" data-testid="invoice-number-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono" />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4">
              <div>
                <Label htmlFor="weight" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Weight (kg) *</Label>
                <Input id="weight" name="weight" type="number" step="0.01" min="0.1" value={formData.weight} onChange={handleChange} required data-testid="weight-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                <p className="text-xs text-zinc-500 mt-1">e.g., 0.5 = 500 grams</p>
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

          {/* Seller / Tax Details */}
          <div className="p-6 border-b border-zinc-200">
            <h2 className="text-lg font-bold tracking-tight mb-4">Seller / Tax Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="seller_gst" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Seller GSTIN</Label>
                <Input
                  id="seller_gst"
                  name="seller_gst"
                  value={formData.seller_gst}
                  onChange={handleChange}
                  placeholder="e.g., 27ABCDE1234F1Z5"
                  data-testid="seller-gst-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono"
                />
                <p className="text-xs text-zinc-500 mt-1">Defaults from Settings if not entered</p>
              </div>
            </div>
          </div>

          {/* Payment Details */}
          <div className="p-6">
            <h2 className="text-lg font-bold tracking-tight mb-4">Payment Details</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <Label htmlFor="payment_mode" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">Payment Mode *</Label>
                <Select name="payment_mode" value={formData.payment_mode} onValueChange={(value) => setFormData((prev) => ({ ...prev, payment_mode: value }))}>
                  <SelectTrigger data-testid="payment-mode-select" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="Prepaid">Prepaid</SelectItem>
                    <SelectItem value="COD">Cash on Delivery (COD)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {formData.payment_mode === "COD" && (
                <div>
                  <Label htmlFor="cod_amount" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">COD Amount (₹) *</Label>
                  <Input id="cod_amount" name="cod_amount" type="number" step="0.01" min="0" value={formData.cod_amount} onChange={handleChange} required data-testid="cod-amount-input" className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm" />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="mt-6">
          <Button
            type="submit"
            disabled={loading}
            data-testid="create-shipment-submit-btn"
            className="bg-red-600 text-white px-8 py-3 rounded-sm font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-600 transition-colors"
          >
            {loading ? "Creating Shipment..." : "Create Shipment"}
          </Button>
        </div>
      </form>
    </div>
  );
};

export default CreateShipment;