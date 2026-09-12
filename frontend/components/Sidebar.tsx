"use client";

import React from "react";
import {
  FileText,
  Calculator,
  BookOpen,
  CheckCircle2,
  FolderLock,
  Settings,
  LayoutDashboard,
  Layers,
} from "lucide-react";

interface NavItem {
  name: string;
  icon: React.ElementType;
  badge?: string;
  active?: boolean;
}

export const Sidebar: React.FC = () => {
  const navItems: NavItem[] = [
    { name: "Overview", icon: LayoutDashboard, active: true },
    { name: "Applications", icon: FileText, badge: "Phase 1+" },
    { name: "Document Ingestion", icon: FolderLock, badge: "Phase 2+" },
    { name: "Calculations (DTI/LTV)", icon: Calculator, badge: "Phase 3+" },
    { name: "Guideline RAG", icon: BookOpen, badge: "Phase 4+" },
    { name: "Compliance & Audits", icon: CheckCircle2, badge: "Phase 5+" },
    { name: "Orchestration Graph", icon: Layers, badge: "Phase 6+" },
    { name: "System Settings", icon: Settings },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-slate-900/50 flex flex-col h-[calc(100vh-4rem)] p-4 select-none">
      <div className="space-y-1">
        <p className="px-3 text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
          Navigation
        </p>
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <div
              key={item.name}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm transition font-medium ${
                item.active
                  ? "bg-indigo-600/10 text-indigo-400 border border-indigo-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 cursor-not-allowed"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-4 h-4 shrink-0" />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {item.badge}
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-auto p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-400">
        <p className="font-semibold text-slate-300">Phase 0 Active</p>
        <p className="mt-1 text-slate-500 leading-relaxed">
          Foundation & modular structure ready. Business logic isolated.
        </p>
      </div>
    </aside>
  );
};
