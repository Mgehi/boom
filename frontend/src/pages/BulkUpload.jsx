import { useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Upload, Download, FileText, Check, AlertCircle, Package } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const BulkUpload = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState(null);
  const [downloadingLabels, setDownloadingLabels] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && !selectedFile.name.endsWith(".csv")) {
      toast.error("Please upload a CSV file");
      return;
    }
    setFile(selectedFile);
    setResults(null);
  };

  const handleDownloadTemplate = async () => {
    try {
      const response = await axios.get(`${API}/shipments/bulk/template`, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "bulk_shipment_template.csv";
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Template downloaded");
    } catch (error) {
      toast.error("Failed to download template");
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error("Please select a CSV file");
      return;
    }

    setUploading(true);
    setResults(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post(`${API}/shipments/bulk/upload`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResults(response.data);
      toast.success(`Processed ${response.data.total} orders: ${response.data.success} successful, ${response.data.failed} failed`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDownloadAllShipments = async () => {
    try {
      const response = await axios.get(`${API}/shipments/bulk/download`, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "text/csv" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `shipments_${new Date().toISOString().split("T")[0]}.csv`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Shipments report downloaded");
    } catch (error) {
      toast.error("Failed to download shipments");
    }
  };

  const handleDownloadBulkLabels = async () => {
    if (!results || results.shipments.length === 0) {
      toast.error("No shipments to download labels for");
      return;
    }

    const waybills = results.shipments
      .filter((s) => s.waybill)
      .map((s) => s.waybill)
      .join(",");

    if (!waybills) {
      toast.error("No waybills available for label download");
      return;
    }

    setDownloadingLabels(true);
    try {
      const response = await axios.get(`${API}/shipments/bulk/labels?waybills=${waybills}`, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `bulk_labels_${new Date().toISOString().split("T")[0]}.pdf`;
      link.click();
      window.URL.revokeObjectURL(url);
      toast.success("Labels downloaded");
    } catch (error) {
      toast.error("Failed to download labels");
    } finally {
      setDownloadingLabels(false);
    }
  };

  return (
    <div className="p-8" data-testid="bulk-upload-page">
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2" data-testid="bulk-upload-title">Bulk Shipment Upload</h1>
          <p className="text-zinc-500">Upload multiple shipments at once using CSV</p>
        </div>
        <Button
          onClick={handleDownloadAllShipments}
          data-testid="download-all-shipments-btn"
          className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
        >
          <Download className="w-4 h-4 mr-2" />
          Export All Shipments
        </Button>
      </div>

      <div className="max-w-4xl space-y-6">
        {/* Instructions */}
        <div className="border border-zinc-200 rounded-sm bg-[#FAFAFA] p-6">
          <h2 className="text-lg font-bold tracking-tight mb-3">How it works</h2>
          <ol className="space-y-2 text-sm text-zinc-600 list-decimal list-inside">
            <li>Configure your default sender details in <strong className="text-zinc-900">Settings</strong> first</li>
            <li>Download the CSV template below</li>
            <li>Fill in receiver and package details for each shipment</li>
            <li>Upload the CSV file to create all shipments at once</li>
            <li>Download all generated shipping labels in a single PDF</li>
          </ol>
        </div>

        {/* Template Download */}
        <div className="border border-zinc-200 rounded-sm bg-white p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-bold text-zinc-900 mb-1">Step 1: Download Template</h3>
              <p className="text-sm text-zinc-500">Get the CSV template with sample data</p>
            </div>
            <Button
              onClick={handleDownloadTemplate}
              data-testid="download-template-btn"
              className="bg-zinc-900 text-white hover:bg-zinc-800 rounded-sm"
            >
              <Download className="w-4 h-4 mr-2" />
              Download Template
            </Button>
          </div>
        </div>

        {/* File Upload */}
        <div className="border border-zinc-200 rounded-sm bg-white p-6">
          <h3 className="font-bold text-zinc-900 mb-4">Step 2: Upload Your CSV</h3>
          
          <form onSubmit={handleUpload}>
            <div className="border-2 border-dashed border-zinc-300 rounded-sm p-8 text-center mb-4">
              <Upload className="w-12 h-12 text-zinc-400 mx-auto mb-3" />
              <input
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                data-testid="csv-file-input"
                id="csv-upload"
                className="hidden"
              />
              <label htmlFor="csv-upload" className="cursor-pointer">
                <p className="text-zinc-700 font-medium mb-1">
                  {file ? file.name : "Click to select a CSV file"}
                </p>
                <p className="text-sm text-zinc-500">
                  {file ? `${(file.size / 1024).toFixed(2)} KB` : "or drag and drop"}
                </p>
              </label>
            </div>

            <Button
              type="submit"
              disabled={!file || uploading}
              data-testid="upload-csv-btn"
              className="bg-red-600 text-white hover:bg-red-700 rounded-sm w-full md:w-auto"
            >
              {uploading ? "Processing..." : "Upload & Create Shipments"}
            </Button>
          </form>
        </div>

        {/* Results */}
        {results && (
          <div className="border border-zinc-200 rounded-sm bg-white p-6" data-testid="upload-results">
            <h3 className="font-bold text-zinc-900 mb-4">Upload Results</h3>
            
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="border border-zinc-200 p-4 rounded-sm">
                <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Total</p>
                <p className="text-3xl font-bold text-zinc-900" data-testid="result-total">{results.total}</p>
              </div>
              <div className="border border-zinc-200 p-4 rounded-sm bg-zinc-50">
                <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Success</p>
                <p className="text-3xl font-bold text-zinc-900" data-testid="result-success">{results.success}</p>
              </div>
              <div className="border border-red-200 p-4 rounded-sm bg-red-50">
                <p className="text-xs uppercase tracking-wider text-red-600 mb-1">Failed</p>
                <p className="text-3xl font-bold text-red-700" data-testid="result-failed">{results.failed}</p>
              </div>
            </div>

            {/* Bulk Label Download */}
            {results.success > 0 && (
              <div className="mb-6 p-4 bg-[#FAFAFA] border border-zinc-200 rounded-sm flex items-center justify-between">
                <div>
                  <p className="font-medium text-zinc-900">Download All Labels</p>
                  <p className="text-sm text-zinc-500">Get all {results.success} shipping labels in one PDF</p>
                </div>
                <Button
                  onClick={handleDownloadBulkLabels}
                  disabled={downloadingLabels}
                  data-testid="download-bulk-labels-btn"
                  className="bg-red-600 text-white hover:bg-red-700 rounded-sm"
                >
                  <Download className="w-4 h-4 mr-2" />
                  {downloadingLabels ? "Downloading..." : "Download Labels PDF"}
                </Button>
              </div>
            )}

            {/* Successful Shipments */}
            {results.shipments.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-zinc-900 mb-3 flex items-center gap-2">
                  <Check className="w-4 h-4 text-zinc-900" />
                  Created Shipments
                </h4>
                <div className="border border-zinc-200 rounded-sm overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-[#FAFAFA]">
                      <tr className="border-b border-zinc-200">
                        <th className="px-4 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Order ID</th>
                        <th className="px-4 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Waybill</th>
                        <th className="px-4 py-3 text-left font-medium uppercase tracking-[0.2em] text-xs text-zinc-500">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.shipments.map((s, idx) => (
                        <tr key={idx} className="border-b border-zinc-200 last:border-b-0" data-testid={`bulk-result-row-${idx}`}>
                          <td className="px-4 py-3 mono text-zinc-900">{s.order_id}</td>
                          <td className="px-4 py-3 mono text-zinc-600">{s.waybill || "N/A"}</td>
                          <td className="px-4 py-3">
                            <span className="inline-flex items-center px-2 py-1 rounded-sm text-xs font-medium border bg-zinc-100 text-zinc-900 border-zinc-300">
                              {s.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Errors */}
            {results.errors.length > 0 && (
              <div>
                <h4 className="font-medium text-red-700 mb-3 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Failed Shipments
                </h4>
                <div className="space-y-2">
                  {results.errors.map((err, idx) => (
                    <div key={idx} className="border border-red-200 bg-red-50 p-3 rounded-sm" data-testid={`bulk-error-${idx}`}>
                      <p className="font-medium text-red-900">{err.order_id}</p>
                      <p className="text-sm text-red-700">{err.error}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default BulkUpload;
