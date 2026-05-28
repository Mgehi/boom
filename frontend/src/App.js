import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Dashboard from "@/pages/Dashboard";
import CreateShipment from "@/pages/CreateShipment";
import ShipmentList from "@/pages/ShipmentList";
import ShipmentDetail from "@/pages/ShipmentDetail";
import SchedulePickup from "@/pages/SchedulePickup";
import BulkUpload from "@/pages/BulkUpload";
import Settings from "@/pages/Settings";
import Layout from "@/components/Layout";

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="create-shipment" element={<CreateShipment />} />
            <Route path="bulk-upload" element={<BulkUpload />} />
            <Route path="shipments" element={<ShipmentList />} />
            <Route path="shipments/:id" element={<ShipmentDetail />} />
            <Route path="pickup" element={<SchedulePickup />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
