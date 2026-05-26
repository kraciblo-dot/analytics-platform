"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Activity, ArrowRight, Building, Lock, Mail } from "lucide-react";
import toast from "react-hot-toast";
import { jwtDecode } from "jwt-decode";
import { useAuthStore } from "@/store/useAuthStore";
import { api } from "@/lib/api"; 

interface AuthTokenPayload {
  sub: string;
  org_id: number;
  role: string;
  exp: number;
}

export default function LoginPage() {
  const router = useRouter();
  const setAuth = useAuthStore((state) => state.setAuth);
  
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    organization_name: ""
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        // Login Flow 
        const params = new FormData();
        params.append("username", formData.email);
        params.append("password", formData.password);

        // Using our Axios instance 
        const res = await api.post("/api/auth/login", params);
        const token = res.data.access_token;
        
        // Decode the token to extract the user's role and organization ID
        const decoded = jwtDecode<AuthTokenPayload>(token);
        
        setAuth(
          {
            id: 0, 
            email: decoded.sub,
            role: decoded.role,
            organization_id: decoded.org_id,
          },
          token
        );

        toast.success("Welcome back!");
        router.push("/"); // Now that Zustand has the data, the dashboard will let us in

      } else {
        // Signup Flow
        await api.post("/api/auth/signup", {
          email: formData.email,
          password: formData.password,
          organization_name: formData.organization_name
        });

        toast.success("Account created! Please log in.");
        setIsLogin(true); // Flip back to login mode so they can actually sign in
      }
    } catch (err: any) {
      // Axios wraps errors in err.response.data
      const errorMessage = err.response?.data?.detail || "Authentication failed";
      toast.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
        
        {/* Header */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mb-4">
            <Activity size={28} />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">
            {isLogin ? "Welcome back" : "Create your workspace"}
          </h1>
          <p className="text-gray-500 text-sm mt-2 text-center">
            {isLogin ? "Enter your details to access your dashboard" : "Set up your organization in seconds"}
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Organization Name</label>
              <div className="relative">
                <Building className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <input 
                  required
                  type="text" 
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  placeholder="Acme Corp"
                  value={formData.organization_name}
                  onChange={(e) => setFormData({...formData, organization_name: e.target.value})}
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Work Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input 
                required
                type="email" 
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="you@company.com"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
              <input 
                required
                type="password" 
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>
          </div>

          <button 
            type="submit" 
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg transition-colors flex items-center justify-center gap-2 mt-6 disabled:opacity-70"
          >
            {loading ? "Processing..." : (isLogin ? "Sign In" : "Create Account")}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        {/* Toggle */}
        <div className="mt-6 text-center">
          <button 
            type="button"
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
          </button>
        </div>

      </div>
    </div>
  );
}