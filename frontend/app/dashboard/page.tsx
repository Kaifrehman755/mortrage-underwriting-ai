"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FileText,
  Building,
  RefreshCw,
  Edit3,
  FileCheck,
  CheckCircle2,
  AlertTriangle,
  PlusCircle,
  Eye,
  Layers,
} from "lucide-react";
import { applicationService } from "@/services/applicationService";
import { DashboardStats, MortgageApplication } from "@/types";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { HealthStatus } from "@/components/HealthStatus";
import { formatCurrency, formatDate } from "@/lib/formatters";
import { UnderwritingWorkflowInspector } from "@/components/shared/UnderwritingWorkflowInspector";
import { SubmittedDocumentsRow } from "@/components/shared/SubmittedDocumentsRow";
import { CaseVersionHistory } from "@/components/shared/CaseVersionHistory";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [applications, setApplications] = useState<MortgageApplication[]>([]);
  const [activeApp, setActiveApp] = useState<MortgageApplication | null>(null);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsData, appsData] = await Promise.all([
        applicationService.getDashboardStats(),
        applicationService.getApplications(),
      ]);
      setStats(statsData);
      setApplications(appsData);
      if (appsData && appsData.length > 0) {
        setActiveApp(appsData[0]);
      }
    } catch {
      setStats(null);
      setApplications([]);
      setActiveApp(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Active Loan Case Context Header */}
      {activeApp ? (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
            <div className="space-y-1.5">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-xs font-bold text-slate-800 bg-slate-100 px-2.5 py-0.5 rounded-md border border-slate-200">
                  {activeApp.applicationNumber || activeApp.id || "—"}
                </span>
                <Badge variant="status" status={activeApp.status}>
                  {activeApp.status}
                </Badge>
                {activeApp.riskLevel && (
                  <Badge variant="risk" risk={activeApp.riskLevel}>
                    {activeApp.riskLevel} Risk
                  </Badge>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-slate-950 tracking-tight">
                {activeApp.applicant?.firstName} {activeApp.applicant?.lastName}
              </h1>

              <div className="flex items-center gap-2 text-xs text-slate-600 font-medium pt-0.5">
                <Building className="w-4 h-4 text-slate-400 shrink-0" />
                <span>
                  {activeApp.property?.address?.street || "Property address on file"},{" "}
                  {activeApp.property?.address?.city || ""}, {activeApp.property?.address?.state || ""}{" "}
                  {activeApp.property?.address?.zipCode || ""}
                </span>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              <Link href="/documents">
                <Button
                  variant="outline"
                  size="sm"
                  leftIcon={<Edit3 className="w-3.5 h-3.5 text-slate-600" />}
                >
                  Verify Documents
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

          {/* Top Compact Documents Row */}
          <div className="pt-2 border-t border-slate-100">
            <SubmittedDocumentsRow documents={activeApp.documents} compact={true} />
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex items-center justify-between">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-slate-900">No Active Loan File Selected</h2>
            <p className="text-xs text-slate-500">
              Select an application from the queue below or ingest a new loan intake to begin underwriting.
            </p>
          </div>
          <Link href="/applications/new">
            <Button variant="primary" size="sm" leftIcon={<PlusCircle className="w-3.5 h-3.5" />}>
              Start Intake
            </Button>
          </Link>
        </div>
      )}

      {/* Case Status Notice - Only shown if activeApp has warning/flag */}
      {activeApp?.status === "Needs Review" && (
        <div className="p-4 rounded-xl border border-amber-300 bg-amber-50/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 shadow-2xs">
          <div className="flex items-center space-x-3">
            <div className="px-2.5 py-1 rounded-md bg-amber-200 border border-amber-300 text-amber-950 font-mono font-bold text-xs uppercase tracking-wider shrink-0">
              UNDERWRITING FLAG
            </div>
            <p className="text-xs text-amber-950 font-medium">
              Loan file requires underwriter supervisory verification before final approval.
            </p>
          </div>
          <Link href="/review" className="shrink-0 text-xs font-bold text-amber-900 hover:text-amber-950 underline">
            Open Review Desk →
          </Link>
        </div>
      )}

      {/* 5-Metric Financial KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Loan Amount */}
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Loan Amount</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-950 mt-1 font-mono">
            {activeApp?.loan?.loanAmount ? formatCurrency(activeApp.loan.loanAmount) : "—"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {activeApp?.loan?.loanType ? `${activeApp.loan.loanType} • ${activeApp.loan.interestRate}%` : "Awaiting input"}
          </p>
        </div>

        {/* Loan to Value (LTV) */}
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Loan-to-Value</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-950 mt-1 font-mono">
            {activeApp?.financialMetrics?.ltvPercentage ? `${activeApp.financialMetrics.ltvPercentage}%` : "—"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {activeApp?.financialMetrics?.ltvPercentage
              ? activeApp.financialMetrics.ltvPercentage <= 80
                ? "Standard equity bound (≤80%)"
                : "High LTV tier"
              : "Calculated upon valuation"}
          </p>
        </div>

        {/* Credit Score */}
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Credit Score</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-900 mt-1 font-mono">
            {activeApp?.creditAnalysis?.qualifyingFicoScore || "—"}
          </h3>
          <p className="text-[10px] text-slate-500 font-medium mt-0.5">
            {activeApp?.creditAnalysis?.scoreTier || "Credit bureau tier"}
          </p>
        </div>

        {/* FOIR / DTI */}
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">Debt-to-Income (DTI)</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-950 mt-1 font-mono">
            {activeApp?.financialMetrics?.backEndDti ? `${activeApp.financialMetrics.backEndDti}%` : "—"}
          </h3>
          <p className="text-[10px] text-slate-500 mt-0.5">
            {activeApp?.financialMetrics?.frontEndDti
              ? `Front: ${activeApp.financialMetrics.frontEndDti}% • Back: ${activeApp.financialMetrics.backEndDti}%`
              : "Computed from verified debt"}
          </p>
        </div>

        {/* Disposition / Decision */}
        <div className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-400 transition">
          <p className="text-[11px] font-semibold text-slate-500 uppercase">File Disposition</p>
          <h3 className="text-xl sm:text-2xl font-black text-slate-900 mt-1 font-mono">
            {activeApp?.status || "—"}
          </h3>
          <p className="text-[10px] text-slate-500 font-medium mt-0.5">
            {activeApp?.isDemoData ? "Demo Record Active" : "Operational Record"}
          </p>
        </div>
      </div>

      {/* Deterministic Underwriting Pipeline Stage Inspector */}
      <UnderwritingWorkflowInspector application={activeApp} />

      {/* Lower Section: Revision History & Documents */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-6">
          <CaseVersionHistory
            applicationId={activeApp?.applicationNumber || activeApp?.id}
            auditTrail={activeApp?.auditTrail}
          />
        </div>
        <div className="lg:col-span-6">
          <SubmittedDocumentsRow documents={activeApp?.documents} compact={false} />
        </div>
      </div>

      {/* System Service Connectivity Status */}
      <HealthStatus />

      {/* Loan Applications Queue Table */}
      <Card
        title="Loan Pipeline Queue"
        subtitle="Active mortgage applications. Select a record to inspect and manage."
        action={
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={loadData}
              leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />}
            >
              Refresh
            </Button>
            <Link href="/applications/new">
              <Button variant="primary" size="sm" leftIcon={<PlusCircle className="w-3.5 h-3.5" />}>
                New Loan File
              </Button>
            </Link>
          </div>
        }
      >
        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] tracking-wider border-y border-slate-200">
              <tr>
                <th className="px-6 py-3">Loan ID</th>
                <th className="px-4 py-3">Applicant Name</th>
                <th className="px-4 py-3">Loan Amount</th>
                <th className="px-4 py-3">Property</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Risk Tier</th>
                <th className="px-4 py-3">Last Modified</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {applications.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-12 text-center text-slate-500">
                    <div className="max-w-md mx-auto space-y-2.5">
                      <p className="text-sm font-bold text-slate-800">Underwriting Pipeline Empty</p>
                      <p className="text-xs text-slate-500 leading-relaxed">
                        No active mortgage applications are currently queued. Incoming loan files from the automated pipeline or newly submitted files will appear here dynamically.
                      </p>
                      <div className="pt-2 flex items-center justify-center gap-3">
                        <Link href="/applications/new">
                          <Button variant="primary" size="sm" leftIcon={<PlusCircle className="w-3.5 h-3.5" />}>
                            Intake Loan File
                          </Button>
                        </Link>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            const sample = applicationService.getSandboxTemplate();
                            setApplications([sample]);
                            setActiveApp(sample);
                          }}
                        >
                          Load Sandbox File
                        </Button>
                      </div>
                    </div>
                  </td>
                </tr>
              ) : (
                applications.map((app) => {
                  const isSelected = activeApp?.id === app.id;
                  return (
                    <tr
                      key={app.id}
                      className={`transition cursor-pointer ${
                        isSelected ? "bg-slate-100/70 font-semibold" : "hover:bg-slate-50"
                      }`}
                      onClick={() => setActiveApp(app)}
                    >
                      <td className="px-6 py-3.5 font-mono text-slate-900 font-bold">
                        {app.id}
                      </td>
                      <td className="px-4 py-3.5">
                        <div>
                          <p className="font-bold text-slate-900">
                            {app.applicant?.firstName} {app.applicant?.lastName}
                          </p>
                          <p className="text-[11px] text-slate-500 font-mono">
                            {app.applicant?.employment?.employerName || "Employer on file"}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3.5 font-mono font-bold text-slate-900">
                        <div>
                          <span>{app.loan?.loanAmount ? formatCurrency(app.loan.loanAmount) : "—"}</span>
                          <p className="text-[10px] text-slate-500 font-normal">
                            {app.loan?.loanType || "Conventional"}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1.5 max-w-xs">
                          <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                          <span className="truncate text-slate-700 font-medium">
                            {app.property?.address?.street || "Property address"},{" "}
                            {app.property?.address?.city || ""}
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge variant="status" status={app.status}>
                          {app.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3.5">
                        <Badge variant="risk" risk={app.riskLevel}>
                          {app.riskLevel}
                        </Badge>
                      </td>
                      <td className="px-4 py-3.5 text-slate-500 text-[11px] font-mono">
                        {formatDate(app.updatedAt)}
                      </td>
                      <td className="px-6 py-3.5 text-right">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setActiveApp(app);
                            }}
                            className={`px-2.5 py-1 text-xs rounded-md border font-semibold transition ${
                              isSelected
                                ? "bg-slate-900 text-white border-slate-900"
                                : "bg-white text-slate-700 hover:bg-slate-100 border-slate-200"
                            }`}
                          >
                            {isSelected ? "Active" : "Select"}
                          </button>
                          <Link href={`/applications/${app.id}`} onClick={(e) => e.stopPropagation()}>
                            <Button variant="secondary" size="sm" leftIcon={<Eye className="w-3.5 h-3.5" />}>
                              View
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
