"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  PlusCircle,
  Eye,
  Building,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { applicationService } from "@/services/applicationService";
import { MortgageApplication, ApplicationStatus, RiskLevel } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { EmptyState } from "@/components/ui/EmptyState";
import { formatCurrency, formatDate } from "@/lib/formatters";

const STATUS_OPTIONS: (ApplicationStatus | "All")[] = [
  "All",
  "Needs Review",
  "Processing",
  "Approved",
  "Denied",
  "Suspended",
  "Draft",
];

const RISK_OPTIONS: (RiskLevel | "All")[] = ["All", "LOW", "MODERATE", "HIGH", "CRITICAL"];

export default function ApplicationsPage() {
  const [applications, setApplications] = useState<MortgageApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "All">("All");
  const [riskFilter, setRiskFilter] = useState<RiskLevel | "All">("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const pageSize = 10;

  const loadApplications = React.useCallback(async () => {
    setLoading(true);
    try {
      const data = await applicationService.getApplications({
        status: statusFilter,
        riskLevel: riskFilter,
        searchQuery,
      });
      setApplications(data);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, riskFilter, searchQuery]);

  useEffect(() => {
    loadApplications();
  }, [loadApplications]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <PageHeader
        title="Mortgage Applications"
        subtitle="Manage, filter, and track loan files across all automated and human underwriting phases."
        breadcrumbs={[{ label: "Applications", href: "/applications" }]}
        demoTag="DEMO DATA"
        actions={
          <Link href="/applications/new">
            <Button variant="primary" size="sm" leftIcon={<PlusCircle className="w-3.5 h-3.5" />}>
              Create New Application
            </Button>
          </Link>
        }
      />

      <DemoBanner
        moduleName="Application Registry"
        message="Displaying sample loan applications representing diverse risk, credit, and DTI profiles."
      />

      {/* Filter and Search Bar */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 flex flex-col md:flex-row md:items-center md:justify-between gap-4 shadow-xs">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by ID, applicant name, or property address..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-slate-800 focus:bg-white transition"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-2">
            <Filter className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-xs text-slate-600 font-semibold">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as ApplicationStatus | "All")}
              className="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-indigo-500"
            >
              {STATUS_OPTIONS.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center space-x-2">
            <span className="text-xs text-slate-600 font-semibold">Risk:</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value as RiskLevel | "All")}
              className="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-indigo-500"
            >
              {RISK_OPTIONS.map((risk) => (
                <option key={risk} value={risk}>
                  {risk}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Applications Table Card */}
      <Card className="p-0 overflow-hidden shadow-xs">
        {applications.length === 0 ? (
          <EmptyState
            title="No Applications Found"
            description="No loan applications matched the selected filter criteria or search query."
            actionText="Reset Filters"
            onAction={() => {
              setStatusFilter("All");
              setRiskFilter("All");
              setSearchQuery("");
            }}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] tracking-wider border-b border-slate-200 font-bold">
                <tr>
                  <th className="px-6 py-3.5">Application ID</th>
                  <th className="px-4 py-3.5">Applicant & Employer</th>
                  <th className="px-4 py-3.5">Loan Type & Amount</th>
                  <th className="px-4 py-3.5">Property Location</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Risk Tier</th>
                  <th className="px-4 py-3.5">DTI / LTV</th>
                  <th className="px-4 py-3.5">Created</th>
                  <th className="px-6 py-3.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {applications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50 transition font-medium">
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">
                      <Link href={`/applications/${app.id}`} className="hover:underline">
                        {app.id}
                      </Link>
                      <p className="text-[10px] text-slate-400 font-normal">{app.applicationNumber}</p>
                    </td>
                    <td className="px-4 py-4">
                      <div>
                        <p className="font-bold text-slate-900">
                          {app.applicant.firstName} {app.applicant.lastName}
                        </p>
                        <p className="text-[11px] text-slate-500 font-mono">
                          {app.applicant.employment.employerName}
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-4 font-mono">
                      <span className="font-bold text-slate-900">
                        {formatCurrency(app.loan.loanAmount)}
                      </span>
                      <p className="text-[11px] text-slate-500">
                        {app.loan.loanType} ({app.loan.rateType})
                      </p>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-1.5 max-w-xs">
                        <Building className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="truncate text-slate-700">
                          {app.property.address.street}, {app.property.address.city}, {app.property.address.state}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant="status" status={app.status}>
                        {app.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-4">
                      <Badge variant="risk" risk={app.riskLevel}>
                        {app.riskLevel}
                      </Badge>
                    </td>
                    <td className="px-4 py-4 font-mono text-[11px]">
                      <span className="text-slate-900 font-semibold">
                        {app.financialMetrics?.backEndDti || 0}% DTI
                      </span>
                      <p className="text-slate-500">
                        {app.financialMetrics?.ltvPercentage || 0}% LTV
                      </p>
                    </td>
                    <td className="px-4 py-4 font-mono text-slate-500 text-[11px]">
                      {formatDate(app.createdAt)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <Link href={`/applications/${app.id}`}>
                        <Button variant="secondary" size="sm" leftIcon={<Eye className="w-3.5 h-3.5" />}>
                          Open File
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination UI */}
        <div className="px-6 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
          <span>
            Showing <strong className="text-slate-800">{applications.length}</strong> loan files
          </span>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm" disabled={currentPage === 1}>
              <ChevronLeft className="w-3.5 h-3.5" />
            </Button>
            <span className="px-2 font-mono text-[11px] font-semibold">Page {currentPage} of 1</span>
            <Button variant="outline" size="sm" disabled={true}>
              <ChevronRight className="w-3.5 h-3.5" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
