import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search, MapPin, Check, X } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const PincodeChecker = () => {
  const [pincode, setPincode] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCheck = async (e) => {
    e.preventDefault();
    if (!pincode || pincode.length !== 6) {
      toast.error("Please enter a valid 6-digit pincode");
      return;
    }

    setLoading(true);
    setResult(null);
    try {
      const response = await axios.get(`${API}/pincode/check?pincode=${pincode}`);
      setResult(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to check pincode");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-zinc-200 rounded-sm bg-white p-6" data-testid="pincode-checker">
      <div className="flex items-center gap-2 mb-4">
        <MapPin className="w-5 h-5 text-zinc-700" />
        <h2 className="text-lg font-bold tracking-tight">Pincode Serviceability</h2>
      </div>
      <p className="text-sm text-zinc-500 mb-4">
        Check if Delhivery can deliver to a specific pincode
      </p>

      <form onSubmit={handleCheck} className="flex gap-3 mb-4">
        <Input
          type="text"
          maxLength="6"
          pattern="[0-9]{6}"
          value={pincode}
          onChange={(e) => setPincode(e.target.value.replace(/\D/g, ""))}
          placeholder="Enter 6-digit pincode"
          data-testid="pincode-input"
          className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm mono"
        />
        <Button
          type="submit"
          disabled={loading}
          data-testid="check-pincode-btn"
          className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
        >
          <Search className="w-4 h-4 mr-2" />
          {loading ? "Checking..." : "Check"}
        </Button>
      </form>

      {result && (
        <div data-testid="pincode-result" className={`border-l-4 ${result.serviceable ? "border-zinc-900 bg-zinc-50" : "border-red-600 bg-red-50"} p-4 rounded-sm`}>
          <div className="flex items-center gap-2 mb-2">
            {result.serviceable ? (
              <Check className="w-5 h-5 text-zinc-900" />
            ) : (
              <X className="w-5 h-5 text-red-600" />
            )}
            <p className="font-bold text-zinc-900">
              {result.serviceable ? "Serviceable" : "Not Serviceable"}
            </p>
          </div>
          
          {result.serviceable && (
            <div className="space-y-2 text-sm">
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div>
                  <p className="text-xs uppercase tracking-wider text-zinc-500">Location</p>
                  <p className="font-medium text-zinc-900" data-testid="pincode-location">{result.city}, {result.state}</p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wider text-zinc-500">District</p>
                  <p className="font-medium text-zinc-900">{result.district}</p>
                </div>
              </div>
              
              <div className="flex flex-wrap gap-2 pt-2">
                {result.cod_available && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-zinc-900 text-white rounded-sm" data-testid="badge-cod">
                    <Check className="w-3 h-3" /> COD Available
                  </span>
                )}
                {result.prepaid_available && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-zinc-900 text-white rounded-sm" data-testid="badge-prepaid">
                    <Check className="w-3 h-3" /> Prepaid Available
                  </span>
                )}
                {result.pickup_available && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium bg-zinc-900 text-white rounded-sm" data-testid="badge-pickup">
                    <Check className="w-3 h-3" /> Pickup Available
                  </span>
                )}
              </div>
            </div>
          )}
          
          {!result.serviceable && (
            <p className="text-sm text-red-700">{result.message}</p>
          )}
        </div>
      )}
    </div>
  );
};

export default PincodeChecker;
