import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Calendar } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const SchedulePickup = () => {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    pickup_location: "",
    pickup_date: "",
    pickup_time: "",
    expected_package_count: 1,
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/pickups`, formData);
      toast.success("Pickup scheduled successfully!");
      setFormData({
        pickup_location: "",
        pickup_date: "",
        pickup_time: "",
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
    <div className="p-8" data-testid="schedule-pickup-page">
      <div className="mb-8">
        <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="schedule-pickup-title">Schedule Pickup</h1>
        <p className="text-zinc-500">Request a pickup for your shipments</p>
      </div>

      <div className="max-w-3xl">
        {/* Hero Banner */}
        <div className="relative h-48 mb-8 rounded-sm overflow-hidden border border-zinc-200">
          <img
            src="https://images.unsplash.com/photo-1577705998148-6da4f3963bc8?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxOTF8MHwxfHNlYXJjaHwzfHxzaGlwcGluZyUyMHBhcmNlbCUyMG1pbmltYWx8ZW58MHx8fHwxNzc5ODc1MDEyfDA&ixlib=rb-4.1.0&q=85"
            alt="Pickup scheduling"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-zinc-900/40 flex items-center justify-center">
            <div className="text-center text-white">
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
              <p className="text-xs text-zinc-500 mt-2">Must match your registered warehouse name exactly</p>
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
                  data-testid="pickup-date-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
                />
              </div>

              <div>
                <Label htmlFor="pickup_time" className="text-xs uppercase tracking-wider text-zinc-600 mb-2 block">
                  Pickup Time *
                </Label>
                <Input
                  id="pickup_time"
                  name="pickup_time"
                  type="time"
                  value={formData.pickup_time}
                  onChange={handleChange}
                  required
                  data-testid="pickup-time-input"
                  className="bg-white border-zinc-200 focus:ring-2 focus:ring-zinc-900 rounded-sm"
                />
              </div>
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