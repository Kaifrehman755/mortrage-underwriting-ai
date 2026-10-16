"use client";

import React from "react";
import Link from "next/link";
import { CheckCircle2, Clock } from "lucide-react";

interface WorkflowProgressProps {
  currentStepId?: string;
  applicationId?: string;
}

export const WORKFLOW_STAGES = [
  { id: "application", name: "Application", href: "/applications" },
  { id: "documents", name: "Documents", href: "/documents" },
  { id: "processing", name: "Processing", href: "/processing" },
  { id: "extraction", name: "Extraction", href: "/extraction" },
  { id: "validation", name: "Validation", href: "/validation" },
  { id: "financial", name: "Financial", href: "/financial" },
  { id: "credit", name: "Credit", href: "/credit" },
  { id: "property", name: "Property", href: "/property" },
  { id: "compliance", name: "Compliance", href: "/compliance" },
  { id: "risk", name: "Risk", href: "/risk" },
  { id: "decision", name: "AI Decision", href: "/decision" },
  { id: "review", name: "Review", href: "/review" },
  { id: "reports", name: "Report", href: "/reports" },
  { id: "audit", name: "Audit Trail", href: "/audit" },
];

export const WorkflowProgress: React.FC<WorkflowProgressProps> = ({
  currentStepId = "financial",
}) => {
  const currentIndex = WORKFLOW_STAGES.findIndex((s) => s.id === currentStepId);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4 mb-6 shadow-xs overflow-x-auto">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-bold text-slate-900 tracking-tight flex items-center gap-1.5">
          <span>Underwriting Pipeline Lifecycle</span>
          <span className="text-[10px] font-mono text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200 font-bold">
            Step {Math.max(1, currentIndex + 1)} of {WORKFLOW_STAGES.length}
          </span>
        </span>
        <span className="text-[11px] font-mono text-slate-500 font-medium">
          Target: Human Supervised Decisioning
        </span>
      </div>

      <div className="flex items-center min-w-[760px] py-2">
        {WORKFLOW_STAGES.map((step, idx) => {
          const isCompleted = idx < currentIndex;
          const isCurrent = idx === currentIndex;

          return (
            <React.Fragment key={step.id}>
              <Link
                href={step.href}
                className={`flex flex-col items-center group cursor-pointer transition select-none ${
                  isCurrent
                    ? "text-indigo-600 font-bold"
                    : isCompleted
                    ? "text-emerald-600 hover:text-emerald-700 font-semibold"
                    : "text-slate-500 hover:text-slate-800"
                }`}
              >
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center border text-xs transition font-semibold ${
                    isCurrent
                      ? "bg-indigo-600 text-white border-indigo-600 ring-4 ring-indigo-100"
                      : isCompleted
                      ? "bg-emerald-100 text-emerald-700 border-emerald-300"
                      : "bg-slate-100 text-slate-600 border-slate-200"
                  }`}
                >
                  {isCompleted ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : isCurrent ? (
                    <Clock className="w-3.5 h-3.5 animate-pulse" />
                  ) : (
                    <span className="text-[10px] font-mono">{idx + 1}</span>
                  )}
                </div>
                <span className="text-[10px] mt-1.5 whitespace-nowrap">{step.name}</span>
              </Link>

              {idx < WORKFLOW_STAGES.length - 1 && (
                <div
                  className={`flex-1 h-[2px] mx-1 transition ${
                    idx < currentIndex ? "bg-emerald-400" : "bg-slate-200"
                  }`}
                />
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
};
