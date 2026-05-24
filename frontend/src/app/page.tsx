"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Activity, LogOut, LayoutDashboard, Upload, Bookmark, Save } from "lucide-react";
import toast from "react-hot-toast";

export default function Dashboard() {
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [savedViews, setSavedViews] = useState<any[]>([]);
  const [newViewName, setNewViewName] = useState("");
  const router = useRouter();

  // 1. Fetch initial chart data & saved dashboards
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsRes, dashboardsRes] = await Promise.all([
          api.get("/analytics/timeseries?event_name=page_view&days_back=7"),
          api.get("/dashboards")
        ]);
        setChartData(analyticsRes.data.data);
        setSavedViews(dashboardsRes.data);
      } catch (err) {
        console.error("Failed to fetch data", err);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [router]);

  // 2. Save Current View
  const handleSaveView = async () => {
    if (!newViewName) return toast.error("Please enter a name for this view");
    try {
      const res = await api.post("/dashboards", {
        name: newViewName,
        configuration: { event_name: "page_view", days_back: 7 }
      });
      setSavedViews([...savedViews, res.data]);
      setNewViewName("");
      toast.success("Dashboard view saved!");
    } catch (err) {
      toast.error("Failed to save view");
    }
  };

  // 3. Secure Logout Handler
  const handleLogout = async () => {
    try {
      await api.post("/auth/logout");
      localStorage.removeItem("access_token");
      router.push("/login");
    } catch (err) {
      console.error("Logout failed");
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-gray-50 text-gray-500">Loading your data...</div>;

  return (
    <div className="min-h-screen bg-gray-50 flex text-black">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 p-6 flex flex-col hidden md:flex">
        <div className="flex items-center gap-3 text-blue-600 mb-10">
          <Activity size={28} />
          <span className="text-xl font-bold text-gray-900">Analytics Platform</span>
        </div>
        
        <nav className="flex-1 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-blue-50 text-blue-700 rounded-lg font-medium transition-colors">
            <LayoutDashboard size={20} /> Overview
          </button>
          <button 
            onClick={() => router.push("/import")}
            className="w-full flex items-center gap-3 px-4 py-3 text-gray-600 hover:bg-gray-50 rounded-lg font-medium transition-colors"
          >
            <Upload size={20} /> Data Import
          </button>

          {/* Saved Views Section */}
          <div className="pt-6 pb-2">
            <h4 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3 px-4">Saved Views</h4>
            {savedViews.length === 0 ? (
              <p className="text-sm text-gray-400 px-4">No saved views yet.</p>
            ) : (
              savedViews.map((view: any) => (
                <button key={view.id} className="w-full flex items-center gap-3 px-4 py-2 text-gray-600 hover:text-blue-600 transition-colors text-sm">
                  <Bookmark size={16} /> {view.name}
                </button>
              ))
            )}
          </div>
        </nav>

        <button onClick={handleLogout} className="flex items-center gap-3 px-4 py-3 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg font-medium transition-colors mt-auto">
          <LogOut size={20} /> Sign Out
        </button>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        <header className="mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Platform Overview</h1>
            <p className="text-gray-500">Real-time metrics for your organization</p>
          </div>
          
          {/* Save View Control */}
          <div className="flex gap-2">
            <input 
              type="text" 
              placeholder="Name this view..." 
              value={newViewName}
              onChange={(e) => setNewViewName(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button onClick={handleSaveView} className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">
              <Save size={16} /> Save
            </button>
          </div>
        </header>

        {/* Chart Widget */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900">Page Views (Last 7 Days)</h3>
          </div>
          <div className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E5E7EB" />
                <XAxis dataKey="date" stroke="#6B7280" tick={{fill: '#6B7280'}} tickMargin={10} />
                <YAxis stroke="#6B7280" tick={{fill: '#6B7280'}} tickMargin={10} />
                <Tooltip contentStyle={{ backgroundColor: '#fff', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                <Line type="monotone" dataKey="count" stroke="#2563EB" strokeWidth={3} dot={{ fill: '#2563EB', strokeWidth: 2, r: 4 }} activeDot={{ r: 6, strokeWidth: 0 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </main>
    </div>
  );
}