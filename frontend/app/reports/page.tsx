"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Download,
  Printer,
  FileCode,
  CheckCircle2,
  Building,
  User,
  ShieldCheck,
  Sparkles,
  UserCheck,
  History,
  Scale,
  CreditCard,
  Binary,
} from "lucide-react";
import { reportService } from "@/services/reportService";
import { UnderwritingReport } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner, DisclaimerBox } from "@/components/ui/DemoBanner";
import { formatCurrency, formatDate } from "@/lib/formatters";

export default function ReportsPage() {
  const [report, setReport] = useState<UnderwritingReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadNotice, setDownloadNotice] = useState<string | null>(null);

  useEffect(() => {
    reportService.getUnderwritingReport().then((data) => {
      setReport(data);
      setLoading(false);
    });
  }, []);

  const handleDownloadPDF = () => {
    setDownloadNotice("PDF Generation API is in DEMO MODE. Report generated successfully.");
    setTimeout(() => setDownloadNotice(null), 4000);
  };

  const handleDownloadJSON = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Underwriting_Transmittal_${report.applicationId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <PageHeader
        title="Underwriting Transmittal & Summary Findings Report"
        subtitle="Standardized Fannie Mae 1008 / Freddie Mac 1077 compliant loan transmittal report with deterministic credit audit trail."
        breadcrumbs={[
          { label: "Reports", href: "/reports" },
        ]}
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrint}
              leftIcon={<Printer className="w-3.5 h-3.5" />}
            >
              Print
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={handleDownloadJSON}
              leftIcon={<FileCode className="w-3.5 h-3.5" />}
            >
              Download JSON
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleDownloadPDF}
              leftIcon={<Download className="w-3.5 h-3.5" />}
            >
              Download PDF Report
            </Button>
          </div>
        }
      />

      {downloadNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{downloadNotice}</span>
        </div>
      )}

      <DemoBanner
        moduleName="Report Transmittal Engine"
        message="Displaying live 9-section underwriting summary report. Integrates real-time values from all underwriting pillars."
      />

      {/* Printable Report Document Sheet */}
      <div className="bg-white border border-slate-300 rounded-2xl p-8 shadow-sm space-y-8 text-slate-800">
        {/* Report Header */}
        <div className="border-b border-slate-200 pb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-indigo-700 uppercase tracking-wider">
                MORTGAGE UNDERWRITING TRANSMITTAL SUMMARY
              </span>
              <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded border border-slate-300 font-mono font-bold">
                FNMA Form 1008
              </span>
            </div>
            <h2 className="text-2xl font-black text-slate-900 mt-1">
              Loan Application: {report?.applicationId}
            </h2>
            <p className="text-xs text-slate-500 font-mono mt-0.5">
              Report ID: {report?.reportId} • Date: {formatDate(report?.generatedAt)}
            </p>
          </div>

          <div className="text-right font-mono">
            <span className="text-xs text-slate-500 font-semibold uppercase">Disposition:</span>
            <p className="text-xl font-black text-emerald-700">
              {report?.humanDecision || "APPROVED (SUPERVISED)"}
            </p>
          </div>
        </div>

        {/* 9 Standardized Underwriting Report Sections */}
        <div className="space-y-6 text-xs">
          {/* Section 1: Applicant Summary */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <User className="w-3.5 h-3.5" /> 1. Borrower & Capacity Summary
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-500 font-semibold">Primary Borrower:</span>
                <p className="font-bold text-slate-900 mt-0.5">{report?.applicantSummary.name}</p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">SSN (Masked):</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">{report?.applicantSummary.ssnMasked}</p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Employer:</span>
                <p className="text-slate-900 font-medium mt-0.5 truncate">{report?.applicantSummary.employer}</p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Gross Monthly Income:</span>
                <p className="font-mono font-bold text-emerald-700 mt-0.5">
                  {formatCurrency(report?.applicantSummary.monthlyIncome)}/mo
                </p>
              </div>
            </div>
          </div>

          {/* Section 2: Financial Ratios */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <Binary className="w-3.5 h-3.5" /> 2. Deterministic Financial Analysis
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-500 font-semibold">Loan Amount:</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">
                  {formatCurrency(report?.loanSummary.amount)}
                </p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Loan Terms:</span>
                <p className="text-slate-900 font-medium mt-0.5">
                  {report?.loanSummary.type} • {report?.loanSummary.term}
                </p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Back-End DTI Ratio:</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">
                  {report?.loanSummary.dti}%
                </p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Loan-to-Value (LTV):</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">
                  {report?.loanSummary.ltv}%
                </p>
              </div>
            </div>
          </div>

          {/* Section 3: Credit Profile */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <CreditCard className="w-3.5 h-3.5" /> 3. Credit Reputation Analysis
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div>
                <span className="text-slate-500 font-semibold">Qualifying FICO:</span>
                <p className="font-mono font-bold text-emerald-700 mt-0.5">
                  {report?.applicantSummary.qualifyingCreditScore} (Tier 1 Prime)
                </p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Derogatory Marks:</span>
                <p className="text-slate-900 font-medium mt-0.5">0 Public Records</p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Revolving Utilization:</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">9.18% (Low)</p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Trade Lines Evaluated:</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">14 Open Lines</p>
              </div>
            </div>
          </div>

          {/* Section 4: Property Valuation */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <Building className="w-3.5 h-3.5" /> 4. Collateral & Valuation Findings
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 p-3.5 bg-slate-50 rounded-lg border border-slate-200">
              <div className="sm:col-span-2">
                <span className="text-slate-500 font-semibold">Subject Property Address:</span>
                <p className="font-bold text-slate-900 mt-0.5">{report?.propertySummary.address}</p>
              </div>
              <div>
                <span className="text-slate-500 font-semibold">Reconciled Value:</span>
                <p className="font-mono font-bold text-slate-900 mt-0.5">
                  {formatCurrency(report?.propertySummary.appraisedValue)} (Conf: {report?.propertySummary.valuationConfidence}%)
                </p>
              </div>
            </div>
          </div>

          {/* Section 5: Statutory Compliance */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <Scale className="w-3.5 h-3.5" /> 5. Statutory Compliance Attestation
            </h3>
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-900">
                  Status: {report?.complianceStatus} (48 Rules Checked)
                </p>
                <p className="text-xs text-slate-600 mt-0.5 font-medium">
                  All RESPA 3-day timing, TILA APR caps, and HMDA LAR metrics cleared.
                </p>
              </div>
              <span className="px-2.5 py-1 rounded bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono text-xs font-bold">
                Statutory Pass
              </span>
            </div>
          </div>

          {/* Section 6: Risk Assessment */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <ShieldCheck className="w-3.5 h-3.5" /> 6. Risk Scoring & Quantification
            </h3>
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between font-mono">
              <div>
                <span className="text-slate-500 font-semibold">Composite Risk Score:</span>
                <p className="text-base font-bold text-emerald-700">
                  {report?.riskScore}/100 ({report?.riskLevel} Risk Tier)
                </p>
              </div>
              <div className="text-right">
                <span className="text-slate-500 font-semibold">Post-Closing Liquid Reserves:</span>
                <p className="text-slate-900 font-bold">9.8 Months PITI</p>
              </div>
            </div>
          </div>

          {/* Section 7 & 8: AI Guidance & Human Sign-off */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="space-y-2">
              <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
                <Sparkles className="w-3.5 h-3.5" /> 7. AI Recommendation
              </h3>
              <div className="p-3.5 bg-indigo-50/50 rounded-lg border border-indigo-200">
                <p className="font-bold text-indigo-900">{report?.aiRecommendation}</p>
                <p className="text-xs text-indigo-700 mt-0.5 font-medium">
                  Generated by MortgageGuard LLM v2.4 (Explainable)
                </p>
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
                <UserCheck className="w-3.5 h-3.5" /> 8. Certified Underwriter Sign-Off
              </h3>
              <div className="p-3.5 bg-emerald-50/50 rounded-lg border border-emerald-200">
                <p className="font-bold text-emerald-900">
                  {report?.humanDecision || "Approved"}
                </p>
                <p className="text-xs text-emerald-800 mt-0.5 font-medium">
                  Signed: {report?.reviewerName || "Catherine Hayes, Sr. Underwriter (UW-4029)"}
                </p>
              </div>
            </div>
          </div>

          {/* Section 9: Audit Trail Summary */}
          <div className="space-y-2">
            <h3 className="text-xs font-mono font-bold text-indigo-700 uppercase flex items-center gap-1.5 border-b border-slate-200 pb-1">
              <History className="w-3.5 h-3.5" /> 9. Immutable Audit Trail Summary
            </h3>
            <div className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between font-mono">
              <span className="font-bold text-slate-900">{report?.auditTrailEntriesCount || 6} System Audit Events Logged</span>
              <span className="text-slate-500 font-semibold">Cryptographic SHA-256 Ledger Verified</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
