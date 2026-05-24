"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Papa from "papaparse";
import toast from "react-hot-toast";
import { api } from "@/lib/api";
import { UploadCloud, ArrowLeft, FileType } from "lucide-react";

export default function ImportPage() {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const router = useRouter();

  const processFile = (file: File) => {
    if (file.type !== "text/csv" && !file.name.endsWith(".csv")) {
      toast.error("Please upload a valid CSV file");
      return;
    }

    setIsUploading(true);
    const loadingToast = toast.loading("Parsing and uploading data...");

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        try {
          // Format the parsed CSV data to match our FastAPI Pydantic schema
          const formattedEvents = results.data.map((row: any) => ({
            event_name: row.event_name,
            timestamp: row.timestamp || new Date().toISOString(),
            // Safely parse the JSON string back into an object
            properties: row.properties ? JSON.parse(row.properties) : {}
          }));

          // Send the batch payload to our backend
          await api.post("/events/ingest", { events: formattedEvents });

          toast.success(`Successfully imported ${formattedEvents.length} events!`, { id: loadingToast });
          
          // Route back to the dashboard to see the new data
          setTimeout(() => router.push("/"), 1500);

        } catch (error) {
          console.error("Upload failed", error);
          toast.error("Failed to ingest data. Check your CSV format.", { id: loadingToast });
        } finally {
          setIsUploading(false);
        }
      },
      error: () => {
        toast.error("Error reading the file", { id: loadingToast });
        setIsUploading(false);
      }
    });
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8 text-black">
      <button 
        onClick={() => router.push("/")}
        className="flex items-center gap-2 text-gray-500 hover:text-gray-900 mb-8 transition-colors"
      >
        <ArrowLeft size={20} /> Back to Dashboard
      </button>

      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Import Historical Data</h1>
        <p className="text-gray-500 mb-8">Upload a CSV file to backfill your analytics dashboard. Required columns: event_name, timestamp, properties.</p>

        {/* Drag and Drop Zone */}
        <div 
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-16 text-center transition-all ${
            isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-white hover:border-gray-400"
          } ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
        >
          <div className="flex justify-center mb-4 text-blue-500">
            <UploadCloud size={64} />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">
            Drag and drop your CSV file here
          </h3>
          <p className="text-gray-500 mb-6">or click the button below to browse your files</p>
          
          <label className="cursor-pointer bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition-colors">
            Browse Files
            <input 
              type="file" 
              accept=".csv" 
              className="hidden" 
              onChange={(e) => e.target.files && processFile(e.target.files[0])}
            />
          </label>
        </div>

        {/* Format Guide */}
        <div className="mt-8 bg-white p-6 rounded-xl border border-gray-200">
          <div className="flex items-center gap-2 text-gray-900 font-semibold mb-4">
            <FileType size={20} className="text-blue-500"/>
            <h3>Accepted CSV Format</h3>
          </div>
          <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm overflow-x-auto">
            event_name,timestamp,properties<br/>
            page_view,2026-05-24T10:00:00Z,"{`{"browser":"Chrome","path":"/pricing"}`}"<br/>
            button_click,2026-05-24T10:05:00Z,"{`{"button_id":"checkout"}`}"
          </div>
        </div>
      </div>
    </div>
  );
}