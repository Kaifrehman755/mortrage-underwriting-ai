"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  AlertTriangle,
  FolderLock,
  CreditCard,
  Building,
  Scale,
  ArrowRight,
  ShieldAlert,
  Clock,
  Layers,
} from "lucide-react";
import { MortgageApplication } from "@/types";
import { formatCurrency } from "@/lib/formatters";

interface WorkflowInspectorProps {
  application?: MortgageApplication | null;
}

export type StageId = "documents" | "financial" | "credit" | "property" | "compliance" | "decision";

export const UnderwritingWorkflowInspector: React.FC<WorkflowInspectorProps> = ({ application }) => {
  const [activeStage, setActiveStage] = useState<StageId>("property");

  if (!application) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-xs text-center space-y-2">
        <Layers className="w-8 h-8 text-slate-400 mx-auto" />
        <p className="text-sm font-bold text-slate-800">No active loan file loaded</p>
        <p className="text-xs text-slate-500">Select or ingest a loan application to view underwriting workflow stages.</p>
      </div>
    );
  }

  const docCount = application.documents?.length || 0;
  const fico = application.creditAnalysis?.qualifyingFicoScore;
  const propertyVal = application.property?.estimatedAppraisedValue || 0;
  const dti = application.financialMetrics?.backEndDti;
  const complianceStatus = application.complianceSummary?.overallStatus || "Pending";
  const decisionStatus = application.status || "In Review";

  const stages = [
    {
      id: "documents" as StageId,
      name: "Document Ingestion",
      statusText: docCount > 0 ? `${docCount} documents ingested` : "No documents attached",
      icon: FolderLock,
      isComplete: docCount > 0,
      badge: docCount > 0 ? "VERIFIED" : "PENDING",
    },
    {
      id: "financial" as StageId,
      name: "Financial & DTI",
      statusText: dti ? `Back-end DTI ${dti}%` : "Ratios not computed",
      icon: Scale,
      isComplete: !!dti,
      badge: dti ? (dti <= 43 ? "WITHIN LIMIT" : "FLAGGED") : "PENDING",
    },
    {
      id: "credit" as StageId,
      name: "Credit Evaluation",
      statusText: fico ? `Qualifying score: ${fico}` : "Credit report pending",
      icon: CreditCard,
      isComplete: !!fico,
      badge: fico ? (fico >= 680 ? "PRIME" : "REVIEW") : "PENDING",
    },
    {
      id: "property" as StageId,
      name: "Collateral Valuation",
      statusText: propertyVal > 0 ? `${formatCurrency(propertyVal)} Appraised` : "No appraisal on file",
      icon: Building,
      isComplete: propertyVal > 0,
      badge: propertyVal > 0 ? "VERIFIED" : "AWAITING APPRAISAL",
    },
    {
      id: "compliance" as StageId,
      name: "Regulatory Compliance",
      statusText: `Statutory status: ${complianceStatus}`,
      icon: Scale,
      isComplete: complianceStatus === "Passed",
      badge: complianceStatus.toUpperCase(),
    },
    {
      id: "decision" as StageId,
      name: "Underwriting Adjudication",
      statusText: `Disposition: ${decisionStatus}`,
      icon: CheckCircle2,
      isComplete: decisionStatus === "Approved",
      badge: decisionStatus.toUpperCase(),
    },
  ];

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
      {/* Title Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 gap-2">
        <div>
          <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500">
            DETERMINISTIC UNDERWRITING PIPELINE
          </span>
          <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
            Workflow Evaluation Stages
          </h3>
        </div>
        <div className="text-xs font-mono text-slate-500">
          File: <strong className="text-slate-900">{application.applicationNumber || application.id}</strong>
        </div>
      </div>

      {/* 2-Column Workflow Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 pt-1">
        {/* Left Column: Interactive Stage List */}
        <div className="lg:col-span-5 space-y-2">
          {stages.map((stage, idx) => {
            const Icon = stage.icon;
            const isSelected = activeStage === stage.id;

            return (
              <div
                key={stage.id}
                onClick={() => setActiveStage(stage.id)}
                className={`p-3 rounded-xl border transition-all cursor-pointer flex items-center justify-between ${
                  isSelected
                    ? "bg-slate-100 border-slate-400 ring-2 ring-slate-200 shadow-xs"
                    : "bg-white hover:bg-slate-50 border-slate-200"
                }`}
              >
                <div className="flex items-center space-x-3 min-w-0">
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 border ${
                      stage.isComplete
                        ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                        : "bg-slate-100 text-slate-500 border-slate-300"
                    }`}
                  >
                    {stage.isComplete ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    ) : (
                      <Clock className="w-4 h-4 text-slate-500" />
                    )}
                  </div>
                  <div className="truncate">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900 truncate">
                        {stage.name}
                      </span>
                      <span className="text-[9px] font-mono px-1.5 py-0.2 rounded font-bold uppercase tracking-tight bg-slate-100 text-slate-700 border border-slate-200">
                        {stage.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate mt-0.5 font-medium">
                      {stage.statusText}
                    </p>
                  </div>
                </div>

                <div className="shrink-0 text-slate-400 pl-2">
                  <span className="text-[10px] font-mono font-semibold">{idx + 1}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Column: Stage Findings Card */}
        <div className="lg:col-span-7">
          <div className="h-full bg-slate-50/70 border border-slate-200 rounded-xl p-5 flex flex-col justify-between">
            <div className="space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-200">
                <div>
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-500 font-bold block">
                    STAGE AUDIT &amp; FINDINGS
                  </span>
                  <h4 className="text-base font-extrabold text-slate-900 capitalize">
                    {activeStage === "documents" && "Document Extraction & Ingestion"}
                    {activeStage === "financial" && "Financial Metrics & Ratios"}
                    {activeStage === "credit" && "Credit Bureau & Trade Line Evaluation"}
                    {activeStage === "property" && "Collateral & Property Valuation"}
                    {activeStage === "compliance" && "Statutory Compliance Assessment"}
                    {activeStage === "decision" && "Underwriting Adjudication"}
                  </h4>
                </div>
              </div>

              {/* Dynamic Content based on selected stage */}
              {activeStage === "documents" && (
                <div className="space-y-3 text-xs text-slate-700">
                  <p className="font-semibold text-slate-900">
                    Source Documents Count: {docCount}
                  </p>
                  <ul className="space-y-1.5 font-medium text-slate-600">
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-slate-500" />
                      <span>OCR Data Ingestion &amp; Field Normalization completed</span>
                    </li>
                    <li className="flex items-center gap-2">
                      <CheckCircle2 className="w-3.5 h-3.5 text-slate-500" />
                      <span>Cross-document identity verification completed</span>
                    </li>
                  </ul>
                </div>
              )}

              {activeStage === "financial" && (
                <div className="space-y-3 text-xs text-slate-700">
                  <div className="grid grid-cols-2 gap-3 bg-white p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block uppercase">Back-End DTI</span>
                      <strong className="text-sm font-mono text-slate-900">{dti ? `${dti}%` : "—"}</strong>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block uppercase">Monthly Gross</span>
                      <strong className="text-sm font-mono text-slate-900">
                        {application.financialMetrics?.grossMonthlyIncome
                          ? formatCurrency(application.financialMetrics.grossMonthlyIncome)
                          : "—"}
                      </strong>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    Calculated using standard deterministic capacity formulas.
                  </p>
                </div>
              )}

              {activeStage === "credit" && (
                <div className="space-y-3 text-xs text-slate-700">
                  <div className="grid grid-cols-2 gap-3 bg-white p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block uppercase">Qualifying Score</span>
                      <strong className="text-sm font-mono text-slate-900">{fico || "—"}</strong>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block uppercase">Score Tier</span>
                      <strong className="text-sm text-slate-900">
                        {application.creditAnalysis?.scoreTier || "Pending"}
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {activeStage === "property" && (
                <div className="space-y-3 text-xs text-slate-700">
                  <div className="grid grid-cols-2 gap-3 bg-white p-3 rounded-lg border border-slate-200">
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block uppercase">Appraised Value</span>
                      <strong className="text-sm font-mono text-slate-900">
                        {propertyVal > 0 ? formatCurrency(propertyVal) : "—"}
                      </strong>
                    </div>
                    <div>
                      <span className="text-[10px] font-mono text-slate-400 block uppercase">LTV Ratio</span>
                      <strong className="text-sm font-mono text-slate-900">
                        {application.financialMetrics?.ltvPercentage
                          ? `${application.financialMetrics.ltvPercentage}%`
                          : "—"}
                      </strong>
                    </div>
                  </div>
                  <p className="text-[11px] text-slate-500">
                    {propertyVal > 0
                      ? "Collateral verified against appraisal documentation."
                      : "No certified appraisal recorded on file yet."}
                  </p>
                </div>
              )}

              {activeStage === "compliance" && (
                <div className="space-y-2 text-xs text-slate-600">
                  <p className="font-semibold text-slate-900">Overall: {complianceStatus}</p>
                  <p className="text-[11px] text-slate-500">
                    Evaluated against statutory guidelines (RESPA, TILA, ATR/QM).
                  </p>
                </div>
              )}

              {activeStage === "decision" && (
                <div className="space-y-2 text-xs text-slate-600">
                  <p className="font-semibold text-slate-900">Current Status: {decisionStatus}</p>
                  <p className="text-[11px] text-slate-500">
                    Sign-off authority belongs to the certified underwriting officer.
                  </p>
                </div>
              )}
            </div>

            {/* Deep Link to Section */}
            <div className="pt-4 border-t border-slate-200 mt-4">
              <Link
                href={
                  activeStage === "documents"
                    ? "/documents"
                    : activeStage === "financial"
                    ? "/financial"
                    : activeStage === "credit"
                    ? "/credit"
                    : activeStage === "property"
                    ? "/property"
                    : activeStage === "compliance"
                    ? "/compliance"
                    : "/review"
                }
                className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-900 hover:text-slate-700 transition"
              >
                <span>Navigate to full module →</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
