"use client";

import React, { useEffect, useState } from "react";
import { healthService } from "@/services/healthService";
import { HealthStatusResponse } from "@/types";
import { Activity, Database, Server, RefreshCw, AlertCircle, CheckCircle2 } from "lucide-react";

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await healthService.getHealthStatus();
      setHealth(data);
      setLastUpdated(new Date().toLocaleTimeString());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to connect to backend API");
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000); // Poll every 15s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-semibold text-white">System Health & Connectivity</h2>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="flex items-center space-x-1.5 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1.5 rounded-md border border-slate-700 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Backend Status Card */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Server className="w-4 h-4 text-slate-400" />
              FastAPI Backend
            </span>
            {health?.status === "healthy" ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" /> Healthy
              </span>
            ) : error ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-rose-500/10 text-rose-400 border border-rose-500/20">
                <AlertCircle className="w-3 h-3" /> Offline
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
                Checking...
              </span>
            )}
          </div>
          <div className="mt-3">
            <p className="text-xs text-slate-400 font-mono truncate">
              Service: <span className="text-slate-200">{health?.service || "mortgage-underwriting-api"}</span>
            </p>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Version: <span className="text-slate-200">{health?.version || "0.1.0"}</span>
            </p>
          </div>
        </div>

        {/* PostgreSQL Status Card */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
              <Database className="w-4 h-4 text-slate-400" />
              PostgreSQL
            </span>
            {health?.database === "connected" ? (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <CheckCircle2 className="w-3 h-3" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-slate-500/10 text-slate-400 border border-slate-600">
                {health?.database || "Standby"}
              </span>
            )}
          </div>
          <div className="mt-3">
            <p className="text-xs text-slate-400 font-mono">
              Environment: <span className="text-slate-200">{health?.environment || "development"}</span>
            </p>
            <p className="text-xs text-slate-400 font-mono mt-0.5">
              Driver: <span className="text-slate-200">asyncpg / SQLAlchemy</span>
            </p>
          </div>
        </div>

        {/* Sync & Connection Info */}
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg p-4 sm:col-span-2 lg:col-span-1">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 font-medium">Heartbeat Status</span>
            <span className="text-[10px] font-mono text-slate-500">Auto-poll 15s</span>
          </div>
          <div className="mt-3">
            <p className="text-xs text-slate-400">
              Last Verified:{" "}
              <span className="text-slate-200 font-mono">{lastUpdated || "Initializing..."}</span>
            </p>
            {error && (
              <p className="text-xs text-rose-400 mt-1 line-clamp-1" title={error}>
                Error: {error}
              </p>
            )}
            {!error && health && (
              <p className="text-xs text-emerald-400 mt-1">CORS & REST Channel Active</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
