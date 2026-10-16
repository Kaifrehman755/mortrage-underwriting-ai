"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  Activity,
  CheckCircle2,
  Search,
  Building2,
} from "lucide-react";
import { healthService } from "@/services/healthService";
import { HealthStatusResponse } from "@/types";

export const Header: React.FC = () => {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthStatusResponse | null>(null);
  const [showNotifications, setShowNotifications] = useState(false);

  useEffect(() => {
    healthService
      .getHealthStatus()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  return (
    <header className="h-16 border-b border-slate-200 bg-white/95 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between sticky top-0 z-10 shadow-xs">
      {/* Left: Clean Institutional Brand Title */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2.5">
          <div className="p-1.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200 shadow-2xs">
            <Building2 className="w-4 h-4 text-slate-700" />
          </div>
          <div>
            <span className="text-sm font-bold tracking-tight text-slate-950 block leading-tight">
              Mortgage Underwriting Desk
            </span>
            <span className="text-[10px] text-slate-500 font-mono tracking-tight block">
              Financial Risk &amp; Regulatory Compliance
            </span>
          </div>
        </div>
      </div>

      {/* Center Search */}
      <div className="hidden md:flex items-center max-w-sm w-full mx-4">
        <div className="relative w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by loan file number, borrower, or property..."
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 focus:bg-white transition"
          />
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center space-x-3">
        {/* Backend API Connectivity Pill */}
        <div
          className="flex items-center space-x-2 text-xs text-slate-700 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200 select-none cursor-default"
          title={`Backend: ${health?.service || "Local Pipeline"} (${health?.status || "Ready"})`}
        >
          {health?.status === "healthy" ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span className="hidden sm:inline font-mono text-[11px] font-semibold text-emerald-800">
                Agent API Online
              </span>
            </>
          ) : (
            <>
              <Activity className="w-3.5 h-3.5 text-slate-500" />
              <span className="hidden sm:inline font-mono text-[11px] font-semibold text-slate-600">
                Direct Integration
              </span>
            </>
          )}
        </div>

        {/* Notifications */}
        <div className="relative">
          <button
            type="button"
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="System notifications"
            className="p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition relative cursor-pointer"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-emerald-600 rounded-full ring-2 ring-white" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 bg-white border border-slate-200 rounded-xl shadow-xl p-4 z-50 animate-in fade-in">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2 mb-3">
                <span className="text-xs font-semibold text-slate-900">Underwriting Queue Notices</span>
                <span className="text-[10px] font-mono font-bold text-slate-600 bg-slate-100 px-2 py-0.5 rounded">Active</span>
              </div>
              <div className="space-y-2.5 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800">
                  <p className="font-semibold text-[11px] text-slate-900">Asset Verification Required</p>
                  <p className="text-[10px] text-slate-600 mt-0.5">
                    Loan file documentation pending sourcing verification letter.
                  </p>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-800">
                  <p className="font-semibold text-[11px] text-slate-900">Collateral Appraisal Flag</p>
                  <p className="text-[10px] text-slate-600 mt-0.5">
                    Automated valuation model requires physical inspection sign-off.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* User / Underwriter Profile Indicator */}
        <div className="flex items-center space-x-2 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shadow-xs">
            UW
          </div>
          <div className="hidden lg:block text-left">
            <p className="text-xs font-semibold text-slate-900 leading-tight">Underwriter Officer</p>
            <p className="text-[10px] text-slate-500 font-mono">Credit Risk Desk</p>
          </div>
        </div>
      </div>
    </header>
  );
};
