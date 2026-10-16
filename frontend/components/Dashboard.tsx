"use client";

import React from "react";
import { HealthStatus } from "@/components/HealthStatus";
import {
  FileCheck2,
  Cpu,
  Scale,
  Sparkles,
  ShieldCheck,
  FolderGit2,
  Network,
  Binary,
} from "lucide-react";

export const Dashboard: React.FC = () => {
  const pipelineStages = [
    {
      title: "1. Document Ingestion",
      desc: "Multi-modal OCR & classification for W-2, 1040, paystubs, and bank statements.",
      icon: FileCheck2,
      phase: "Phase 1-2",
      status: "Architecture Ready",
    },
    {
      title: "2. Financial Calculations",
      desc: "Deterministic computation of DTI, LTV, CLTV, DSCR, and qualifying FICO tiers.",
      icon: Binary,
      phase: "Phase 3",
      status: "Modules Ready",
    },
    {
      title: "3. Regulatory RAG",
      desc: "FNMA Selling Guide & FHLMC guideline retrieval with dense embeddings & reranking.",
      icon: Sparkles,
      phase: "Phase 4",
      status: "Pipeline Ready",
    },
    {
      title: "4. Statutory Compliance",
      desc: "Deterministic rule evaluation for RESPA, TILA, HMDA LAR, and Fair Lending flags.",
      icon: Scale,
      phase: "Phase 5",
      status: "Rules Ready",
    },
    {
      title: "5. LangGraph Orchestration",
      desc: "Multi-agent coordination graph with human-in-the-loop review routing.",
      icon: Network,
      phase: "Phase 6",
      status: "Graph Ready",
    },
    {
      title: "6. Audit & PDF Findings",
      desc: "Immutable audit logs and natural-language Underwriting Transmittal Summaries.",
      icon: ShieldCheck,
      phase: "Phase 7",
      status: "Templates Ready",
    },
  ];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-indigo-50 via-white to-blue-50 border border-indigo-200 rounded-2xl p-6 relative overflow-hidden shadow-sm">
        <div className="relative z-10">
          <div className="flex items-center space-x-2 text-indigo-700 text-xs font-mono font-bold mb-2">
            <Cpu className="w-4 h-4" />
            <span>FOUNDATION PHASE 0 COMPLETED</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            AI Mortgage Underwriting Automation System
          </h1>
          <p className="text-slate-600 text-sm mt-1 max-w-3xl leading-relaxed font-medium">
            Clean architectural skeleton established. API endpoints, async PostgreSQL engine,
            Pydantic validation, structured logging, exception handlers, Next.js shell, and Docker Compose are configured.
          </p>
        </div>
      </div>

      {/* Live System Health */}
      <HealthStatus />

      {/* Pipeline Architecture Roadmap */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <FolderGit2 className="w-4 h-4 text-indigo-600" />
              Underwriting Pipeline Modules
            </h2>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              Future modular components isolated by domain and ready for incremental implementation.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pipelineStages.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.title}
                className="bg-white border border-slate-200 shadow-sm rounded-xl p-5 hover:border-indigo-300 hover:shadow-md transition"
              >
                <div className="flex items-start justify-between">
                  <div className="p-2.5 bg-indigo-50 rounded-lg border border-indigo-200">
                    <Icon className="w-4 h-4 text-indigo-600" />
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                    {stage.phase}
                  </span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 mt-3">{stage.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{stage.desc}</p>

                <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500 font-mono font-medium">
                  <span>Status:</span>
                  <span className="text-indigo-700 font-bold">{stage.status}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
