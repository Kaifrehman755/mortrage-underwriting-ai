"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  FolderLock,
  Binary,
  CreditCard,
  Building,
  Scale,
  CheckCircle2,
  FileCheck,
  ChevronRight,
  Edit3,
} from "lucide-react";
import { applicationService } from "@/services/applicationService";
import { MortgageApplication } from "@/types";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { formatCurrency } from "@/lib/formatters";
import { UnderwritingWorkflowInspector } from "@/components/shared/UnderwritingWorkflowInspector";
import { SubmittedDocumentsRow } from "@/components/shared/SubmittedDocumentsRow";
import { CaseVersionHistory } from "@/components/shared/CaseVersionHistory";

export default function ApplicationDetailPage() {
  const params = useParams();
  const id = typeof params.id === "string" ? params.id : "";

  const [app, setApp] = useState<MortgageApplication | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (id) {
      applicationService.getApplicationById(id).then((data) => {
        setApp(data);
        setLoading(false);
      });
    }
  }, [id]);

  if (loading) {
    return (
      <div className="p-12 text-center text-slate-500 font-medium">
        Loading loan application file...
      </div>
    );
  }

  if (!app) {
    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3 max-w-md mx-auto my-12 shadow-sm">
        <h2 className="text-lg font-bold text-slate-900">Application File Not Found</h2>
        <p className="text-xs text-slate-500">
          The requested application record ({id}) was not found in the active database.
        </p>
        <div className="pt-2">
          <Link href="/applications">
            <Button variant="primary" size="sm">
              Return to Pipeline Queue
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Top Application Context Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2.5 py-0.5 rounded-md border border-slate-200">
                {app.applicationNumber || app.id}
              </span>
              <Badge variant="status" status={app.status}>
                {app.status}
              </Badge>
              {app.riskLevel && (
                <Badge variant="risk" risk={app.riskLevel}>
                  {app.riskLevel} Risk
                </Badge>
              )}
            </div>

            <h1 className="text-2xl sm:text-3xl font-black text-slate-950 tracking-tight">
              {app.applicant?.firstName} {app.applicant?.lastName}
            </h1>

            <div className="flex items-center gap-2 text-xs text-slate-600 font-medium pt-0.5">
              <Building className="w-4 h-4 text-slate-400 shrink-0" />
              <span>
                {app.property?.address?.street || "Property on record"},{" "}
                {app.property?.address?.city || ""}, {app.property?.address?.state || ""}{" "}
                {app.property?.address?.zipCode || ""}
              </span>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-2.5 shrink-0">
            <Link href="/documents">
              <Button
                variant="outline"
                size="sm"
                leftIcon={<Edit3 className="w-3.5 h-3.5 text-slate-600" />}
              >
                Inspect Documents
              </Button>
            </Link>
            <Link href="/review">
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<CheckCircle2 className="w-3.5 h-3.5 text-slate-700" />}
              >
                Adjudication Desk
              </Button>
            </Link>
            <Link href="/reports">
              <Button
                variant="primary"
                size="sm"
                leftIcon={<FileCheck className="w-3.5 h-3.5" />}
              >
                Transmittal Report
              </Button>
            </Link>
          </div>
        </div>

        {/* Compact Submitted Documents Chips */}
        <div className="pt-2 border-t border-slate-100">
          <SubmittedDocumentsRow documents={app.documents} compact={true} />
        </div>
      </div>

      {/* 5-Metric Financial KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Loan Amount</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-950 mt-1 font-mono">
            {app.loan?.loanAmount ? formatCurrency(app.loan.loanAmount) : "—"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {app.loan?.loanType} • {app.loan?.interestRate}%
          </p>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Loan to Value</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-950 mt-1 font-mono">
            {app.financialMetrics?.ltvPercentage ? `${app.financialMetrics.ltvPercentage}%` : "—"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {app.financialMetrics?.ltvPercentage && app.financialMetrics.ltvPercentage <= 80
              ? "Safe harbor bound (≤80%)"
              : "Calculated ratio"}
          </p>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Credit Score</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-900 mt-1 font-mono">
            {app.creditAnalysis?.qualifyingFicoScore || "—"}
          </h3>
          <p className="text-[10px] text-slate-500 font-medium mt-0.5">
            {app.creditAnalysis?.scoreTier || "Credit tier"}
          </p>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">FOIR / DTI</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-950 mt-1 font-mono">
            {app.financialMetrics?.backEndDti ? `${app.financialMetrics.backEndDti}%` : "—"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            Back-end debt ratio
          </p>
        </div>

        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">File Status</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-900 mt-1 font-mono">
            {app.status || "—"}
          </h3>
          <p className="text-[10px] text-slate-500 font-medium mt-0.5">
            {app.isDemoData ? "Demo Record" : "Operational Record"}
          </p>
        </div>
      </div>

      {/* Underwriting Pipeline Stage Inspector */}
      <UnderwritingWorkflowInspector application={app} />

      {/* Revision History & Submitted Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <CaseVersionHistory
            applicationId={app.applicationNumber || app.id}
            auditTrail={app.auditTrail}
          />
        </div>
        <div className="lg:col-span-6">
          <SubmittedDocumentsRow documents={app.documents} compact={false} />
        </div>
      </div>

      {/* Domain Navigation Hub Grid */}
      <div>
        <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wider">
          Underwriting Functional Modules
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link href="/documents" className="block group">
            <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-400 hover:shadow-xs transition h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200">
                    <FolderLock className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-bold">
                    {app.documents?.length || 0} Files
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition">
                  Document Repository
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Source documents, income tax returns, paystubs, and bank statements.
                </p>
              </div>
              <div className="flex items-center text-xs font-semibold text-slate-900 mt-4 group-hover:translate-x-0.5 transition-transform">
                <span>Open repository</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          </Link>

          <Link href="/financial" className="block group">
            <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-400 hover:shadow-xs transition h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200">
                    <Binary className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-bold">
                    DTI {app.financialMetrics?.backEndDti ? `${app.financialMetrics.backEndDti}%` : "—"}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition">
                  Financial &amp; Capacity
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Deterministic computations for front-end DTI, back-end DTI, and debt ratios.
                </p>
              </div>
              <div className="flex items-center text-xs font-semibold text-slate-900 mt-4 group-hover:translate-x-0.5 transition-transform">
                <span>View ratios</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          </Link>

          <Link href="/credit" className="block group">
            <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-400 hover:shadow-xs transition h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200">
                    <CreditCard className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-bold">
                    Score {app.creditAnalysis?.qualifyingFicoScore || "—"}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition">
                  Credit Evaluation
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Tri-bureau score analysis, trade line records, and derogatory check.
                </p>
              </div>
              <div className="flex items-center text-xs font-semibold text-slate-900 mt-4 group-hover:translate-x-0.5 transition-transform">
                <span>Inspect credit</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          </Link>

          <Link href="/property" className="block group">
            <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-400 hover:shadow-xs transition h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200">
                    <Building className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-bold">
                    Valuation
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition">
                  Property &amp; Collateral
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Appraisal verification and collateral equity safety bounds.
                </p>
              </div>
              <div className="flex items-center text-xs font-semibold text-slate-900 mt-4 group-hover:translate-x-0.5 transition-transform">
                <span>View valuation</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          </Link>

          <Link href="/compliance" className="block group">
            <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-400 hover:shadow-xs transition h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200">
                    <Scale className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-bold">
                    {app.complianceSummary?.overallStatus || "Pending"}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition">
                  Regulatory Compliance
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  RESPA 3-day timing, TILA APR spread, and Fair Lending statutory rules.
                </p>
              </div>
              <div className="flex items-center text-xs font-semibold text-slate-900 mt-4 group-hover:translate-x-0.5 transition-transform">
                <span>Review compliance</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          </Link>

          <Link href="/review" className="block group">
            <div className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-400 hover:shadow-xs transition h-full flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="p-2.5 rounded-lg bg-slate-100 text-slate-800 border border-slate-200">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono text-slate-700 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 font-bold">
                    Adjudication
                  </span>
                </div>
                <h4 className="text-sm font-bold text-slate-900 group-hover:text-slate-700 transition">
                  Decision Desk
                </h4>
                <p className="text-xs text-slate-500 mt-1">
                  Adjudicate loan disposition, stipulations, and underwriter sign-off.
                </p>
              </div>
              <div className="flex items-center text-xs font-semibold text-slate-900 mt-4 group-hover:translate-x-0.5 transition-transform">
                <span>Open decision desk</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
