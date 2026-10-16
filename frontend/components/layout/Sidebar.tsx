"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  FileText,
  BarChart3,
  ShieldCheck,
  CheckCircle2,
  FileCheck,
  PlusCircle,
  FolderLock,
  Building,
  Scale,
  History,
  Settings,
  HelpCircle,
  ChevronDown,
  Layers,
  Search,
  ExternalLink,
} from "lucide-react";

interface NavItem {
  name: string;
  href: string;
  icon: React.ElementType;
  badge?: string;
  description?: string;
}

export const Sidebar: React.FC = () => {
  const pathname = usePathname();
  const [showWorkspace, setShowWorkspace] = useState(true);
  const [filterQuery, setFilterQuery] = useState("");

  const primaryNavItems: NavItem[] = [
    {
      name: "Underwriting Desk",
      href: "/dashboard",
      icon: LayoutDashboard,
      description: "Active Loan File & Portfolio KPIs",
    },
    {
      name: "Pipeline Queue",
      href: "/applications",
      icon: FileText,
      description: "Loan Registry & Adjudication Filter",
    },
    {
      name: "Income & DTI Underwriting",
      href: "/financial",
      icon: BarChart3,
      description: "Debt Ratios, FOIR & Cash-Flow",
    },
    {
      name: "Credit Risk & Bureau",
      href: "/credit",
      icon: ShieldCheck,
      description: "FICO Analysis & Trade-line Checks",
    },
    {
      name: "Collateral & Valuation",
      href: "/property",
      icon: Building,
      description: "AVM Appraisal & Property Equity",
    },
    {
      name: "Regulatory Compliance",
      href: "/compliance",
      icon: Scale,
      description: "ATR/QM, TRID & Statutory Rules",
    },
    {
      name: "Adjudication & Sign-Off",
      href: "/review",
      icon: CheckCircle2,
      description: "Credit Committee Final Decision",
    },
    {
      name: "Transmittal Reports",
      href: "/reports",
      icon: FileCheck,
      description: "FNMA 1008 Underwriting Transmittal",
    },
  ];

  const workspaceNavItems: NavItem[] = [
    {
      name: "New Loan Intake",
      href: "/applications/new",
      icon: PlusCircle,
      description: "Origination Wizard",
    },
    {
      name: "Document Vault & OCR",
      href: "/documents",
      icon: FolderLock,
      description: "Extracted Verification Records",
    },
    {
      name: "Audit Trail & Logs",
      href: "/audit",
      icon: History,
      description: "Compliance Traceability Log",
    },
    {
      name: "System Config",
      href: "/settings",
      icon: Settings,
      description: "Credit Policy & Rules Engine",
    },
  ];

  const filteredPrimary = primaryNavItems.filter((i) =>
    i.name.toLowerCase().includes(filterQuery.toLowerCase())
  );
  const filteredWorkspace = workspaceNavItems.filter((i) =>
    i.name.toLowerCase().includes(filterQuery.toLowerCase())
  );

  return (
    <aside
      className="w-72 h-screen shrink-0 flex flex-col bg-[#111827] text-slate-200 border-r border-slate-800 shadow-xl select-none z-20"
      aria-label="Navigation Menu"
    >
      {/* Top Institutional Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-[#0e1626]">
        <Link
          href="/dashboard"
          className="flex items-center space-x-2.5 group"
        >
          <div className="p-2 rounded-xl bg-slate-800 text-white shadow-sm group-hover:bg-slate-700 transition">
            <Layers className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <span className="text-xs font-black tracking-widest text-white uppercase block leading-tight">
              MORTGAGE OS
            </span>
            <span className="text-[10px] text-slate-400 font-mono tracking-tight block">
              Risk &amp; Underwriting Desk
            </span>
          </div>
        </Link>
      </div>

      {/* Quick Sector Search Filter */}
      <div className="px-3 pt-3 pb-2 border-b border-slate-800/60">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search underwriting sector..."
            value={filterQuery}
            onChange={(e) => setFilterQuery(e.target.value)}
            className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition"
          />
        </div>
      </div>

      {/* Navigation Items List */}
      <div className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
        <p className="px-3 pt-1 pb-1.5 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold">
          Credit &amp; Risk Underwriting
        </p>

        {filteredPrimary.map((item) => {
          const Icon = item.icon;
          const isActive =
            pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs transition font-medium group ${
                isActive
                  ? "bg-slate-800 text-white font-bold shadow-sm border-l-4 border-emerald-500"
                  : "text-slate-300 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <div className="flex items-center space-x-3 min-w-0">
                <Icon
                  className={`w-4 h-4 shrink-0 transition ${
                    isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-emerald-400"
                  }`}
                />
                <div className="truncate">
                  <span className="block truncate">{item.name}</span>
                  {item.description && (
                    <span className="text-[10px] text-slate-500 font-normal block truncate group-hover:text-slate-400">
                      {item.description}
                    </span>
                  )}
                </div>
              </div>
              {item.badge && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full font-bold bg-slate-800 text-slate-300 border border-slate-700 shrink-0 ml-2">
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}

        {/* WORKSPACE & VAULT Divider */}
        <div className="pt-4 pb-1">
          <div
            className="flex items-center justify-between px-3 text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold cursor-pointer hover:text-slate-300 transition"
            onClick={() => setShowWorkspace(!showWorkspace)}
          >
            <span>Workspace &amp; Vault</span>
            <ChevronDown
              className={`w-3.5 h-3.5 transition-transform ${showWorkspace ? "rotate-0" : "-rotate-90"}`}
            />
          </div>
        </div>

        {showWorkspace &&
          filteredWorkspace.map((item) => {
            const Icon = item.icon;
            const isActive =
              pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2 rounded-xl text-xs transition font-medium group ${
                  isActive
                    ? "bg-slate-800 text-white font-bold shadow-sm border-l-4 border-emerald-500"
                    : "text-slate-400 hover:text-slate-100 hover:bg-slate-800/60"
                }`}
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <Icon
                    className={`w-4 h-4 shrink-0 transition ${
                      isActive ? "text-emerald-400" : "text-slate-400 group-hover:text-emerald-400"
                    }`}
                  />
                  <div className="truncate">
                    <span className="block truncate">{item.name}</span>
                    {item.description && (
                      <span className="text-[10px] text-slate-500 font-normal block truncate group-hover:text-slate-400">
                        {item.description}
                      </span>
                    )}
                  </div>
                </div>
              </Link>
            );
          })}
      </div>

      {/* Footer Support & System Status */}
      <div className="p-3 border-t border-slate-800 space-y-2 bg-[#0b0f19]">
        <Link
          href="/settings"
          className="flex items-center justify-between px-3 py-2 rounded-lg text-xs text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 transition font-medium"
        >
          <div className="flex items-center space-x-2.5">
            <HelpCircle className="w-4 h-4 text-slate-500" />
            <span>Credit Guidelines &amp; Manual</span>
          </div>
          <ExternalLink className="w-3 h-3 text-slate-600" />
        </Link>
        <div className="pt-1 px-3 flex items-center justify-between text-[10px] font-mono text-slate-500">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
            Deterministic Engine
          </span>
          <span className="text-slate-400 font-semibold">Ready</span>
        </div>
      </div>
    </aside>
  );
};
