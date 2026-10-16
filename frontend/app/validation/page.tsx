"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertOctagon,
  AlertTriangle,
  Info,
  CheckCircle2,
  FileText,
  Filter,
  ArrowRight,
  ShieldCheck,
  Check,
  RotateCcw,
} from "lucide-react";
import { documentService } from "@/services/documentService";
import { ValidationIssue, ValidationSeverity, ValidationCategory } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { formatDate } from "@/lib/formatters";

export default function ValidationPage() {
  const [issues, setIssues] = useState<ValidationIssue[]>([]);
  const [severityFilter, setSeverityFilter] = useState<ValidationSeverity | "All">("All");

  const loadIssues = async () => {
    const data = await documentService.getValidationIssues();
    setIssues(data);
  };

  useEffect(() => {
    loadIssues();
  }, []);

  const handleStatusChange = (id: string, newStatus: "Open" | "Acknowledged" | "Resolved" | "Waived") => {
    setIssues((prev) =>
      prev.map((issue) =>
        issue.id === id ? { ...issue, status: newStatus } : issue
      )
    );
  };

  const filteredIssues =
    severityFilter === "All"
      ? issues
      : issues.filter((i) => i.severity === severityFilter);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Rule-Based Cross-Document Validation Engine"
        subtitle="Automated cross-checking for missing documentation, contradictory income figures, low OCR confidence, and guideline threshold variances."
        breadcrumbs={[
          { label: "Document Center", href: "/documents" },
          { label: "Validation Engine" },
        ]}
        demoTag="DEMO DATA"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/financial">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to Financial Analysis
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Validation Rules Engine"
        message="Validates structured document extracts against deterministic Fannie Mae / Freddie Mac rules before calculation processing."
      />

      {/* Severity Counters Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Total Rules</p>
            <p className="text-2xl font-bold text-slate-900 mt-1 font-mono">18 Evaluated</p>
          </div>
          <div className="p-2.5 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-600">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-rose-50/70 border border-rose-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-rose-700 font-semibold uppercase tracking-wider">Critical Issues</p>
            <p className="text-2xl font-bold text-rose-700 mt-1 font-mono">
              {issues.filter((i) => i.severity === "CRITICAL").length}
            </p>
          </div>
          <div className="p-2.5 rounded-lg bg-rose-100 border border-rose-300 text-rose-600">
            <AlertOctagon className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-amber-700 font-semibold uppercase tracking-wider">Warnings / Flags</p>
            <p className="text-2xl font-bold text-amber-700 mt-1 font-mono">
              {issues.filter((i) => i.severity === "WARNING").length}
            </p>
          </div>
          <div className="p-2.5 rounded-lg bg-amber-100 border border-amber-300 text-amber-600">
            <AlertTriangle className="w-5 h-5" />
          </div>
        </div>

        <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs text-blue-700 font-semibold uppercase tracking-wider">Informational</p>
            <p className="text-2xl font-bold text-blue-700 mt-1 font-mono">
              {issues.filter((i) => i.severity === "INFO").length}
            </p>
          </div>
          <div className="p-2.5 rounded-lg bg-blue-100 border border-blue-300 text-blue-600">
            <Info className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex items-center space-x-2 bg-white border border-slate-200 shadow-sm rounded-xl p-3 px-4">
        <Filter className="w-4 h-4 text-slate-400" />
        <span className="text-xs text-slate-600 font-semibold uppercase tracking-wider">Filter Severity:</span>
        {(["All", "CRITICAL", "WARNING", "INFO"] as const).map((sev) => (
          <button
            key={sev}
            onClick={() => setSeverityFilter(sev)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              severityFilter === sev
                ? "bg-indigo-600 text-white shadow-sm"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
            }`}
          >
            {sev}
          </button>
        ))}
      </div>

      {/* Validation Issue Cards List */}
      <div className="space-y-3">
        {filteredIssues.map((issue) => (
          <div
            key={issue.id}
            className={`p-5 rounded-xl border shadow-sm transition flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              issue.severity === "CRITICAL"
                ? "bg-rose-50/50 border-rose-200 hover:border-rose-300"
                : issue.severity === "WARNING"
                ? "bg-amber-50/50 border-amber-200 hover:border-amber-300"
                : "bg-white border-slate-200 hover:border-slate-300"
            }`}
          >
            <div className="space-y-1.5 flex-1">
              <div className="flex items-center gap-2">
                <Badge variant="severity" severity={issue.severity}>
                  {issue.severity}
                </Badge>
                <span className="text-[11px] font-mono font-semibold text-slate-500 uppercase">
                  {issue.category}
                </span>
                <span className="text-[11px] text-slate-400 font-mono">• ID: {issue.id}</span>
              </div>

              <h4 className="text-sm font-bold text-slate-900">{issue.title}</h4>
              <p className="text-xs text-slate-600 leading-relaxed">{issue.description}</p>

              <div className="flex flex-wrap items-center gap-3 pt-1 text-[11px] text-slate-500">
                <span className="flex items-center gap-1 font-mono">
                  <FileText className="w-3.5 h-3.5 text-slate-400" />
                  Sources: <strong className="text-slate-700">{issue.sourceDocuments.join(", ")}</strong>
                </span>
                {issue.resolutionNote && (
                  <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-mono font-medium">
                    ✓ Resolution: {issue.resolutionNote}
                  </span>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center space-x-2 shrink-0 pt-2 md:pt-0">
              {issue.status === "Open" ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleStatusChange(issue.id, "Acknowledged")}
                  >
                    Acknowledge
                  </Button>
                  <Button
                    variant="success"
                    size="sm"
                    onClick={() => handleStatusChange(issue.id, "Resolved")}
                    leftIcon={<Check className="w-3.5 h-3.5" />}
                  >
                    Resolve Issue
                  </Button>
                </>
              ) : (
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-lg border border-emerald-200">
                    Status: {issue.status}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleStatusChange(issue.id, "Open")}
                    title="Reopen Issue"
                  >
                    <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                  </Button>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
