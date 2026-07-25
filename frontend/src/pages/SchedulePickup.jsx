import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Calendar } from "lucide-react";

export const SchedulePickup = () => {
  const [loading, setLoading] = useState(false);
  const [defaultPickup, setDefaultPickup] = useState("");
  const [formData, setFormData] = useState({
    pickup_location: "",
    pickup_date: "",
    expected_package_count: 1,
  });

  useEffect(() => {
    // Load default pickup location from settings
    api.get("/settings").then((res) => {
      if (res.data?.pickup_location) {
        setDefaultPickup(res.data.pickup_location);
        setFormData((prev) => ({ ...prev, pickup_location: res.data.pickup_location }));
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
      // Send default pickup_time of "10:00:00" - backend handles it
      await api.post("/pickups", {
        ...formData,
        pickup_time: "10:00:00",
        expected_package_count: parseInt(formData.expected_package_count),
      });
      toast.success("Pickup scheduled successfully!");
      setFormData({
        pickup_location: defaultPickup,
        pickup_date: "",
        expected_package_count: 1,
      });
    } catch (error) {
      console.error("Failed to schedule pickup", error);
      toast.error(error.response?.data?.detail || "Failed to schedule pickup");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 lg:p-8" data-testid="schedule-pickup-page">
      <div className="mb-8">
        <h1 className="text-2xl lg:text-4xl font-bold tracking-tight mb-2" data-testid="schedule-pickup-title">Schedule Pickup</h1>
        <p className="text-zinc-500">Request a pickup for your shipments</p>
      </div>

      <div className="max-w-3xl">
        {/* Hero Banner */}
        <div className="relative h-40 mb-8 rounded-sm overflow-hidden border border-zinc-200 bg-zinc-900">
          <div className="absolute inset-0 flex items-center justify-center text-white">
            <div className="text-center">
              <Calendar className="w-12 h-12 mx-auto mb-3" />
              <h2 className="text-2xl font-bold tracking-tight">Schedule Your Pickup</h2>
            </div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="border border-zinc-200 rounded-sm bg-white p-6">
          <div className="space-y-6">
            <div>
              <Label htmlFor="pickup_location" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">
                Pickup Location *
              </Label>
              <Input
                id="pickup_location"
                name="pickup_location"
                value={formData.pickup_location}
                onChange={handleChange}
                required
                data-testid="pickup-location-input"
                placeholder="Enter your registered warehouse name"
                className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
              />
              <p className="text-xs text-zinc-500 mt-2">Must match your registered warehouse name in Delhivery exactly</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <Label htmlFor="pickup_date" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">
                  Pickup Date *
                </Label>
                <Input
                  id="pickup_date"
                  name="pickup_date"
                  type="date"
                  value={formData.pickup_date}
                  onChange={handleChange}
                  required
                  min={new Date().toISOString().split("T")[0]}
                  data-testid="pickup-date-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
                />
              </div>

              <div>
                <Label htmlFor="expected_package_count" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">
                  Expected Package Count *
                </Label>
                <Input
                  id="expected_package_count"
                  name="expected_package_count"
                  type="number"
                  min="1"
                  value={formData.expected_package_count}
                  onChange={handleChange}
                  required
                  data-testid="package-count-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
                />
              </div>
            </div>
          </div>

          <div className="mt-8">
            <Button
              type="submit"
              disabled={loading}
              data-testid="schedule-pickup-submit-btn"
              className="bg-red-600 text-white px-8 py-3 rounded-sm font-medium hover:bg-red-700 focus:ring-2 focus:ring-red-600 transition-colors"
            >
              {loading ? "Scheduling..." : "Schedule Pickup"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default SchedulePickup;
