"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Scale,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  AlertOctagon,
  Info,
  ArrowRight,
  FileCheck2,
  BookOpen,
} from "lucide-react";
import { complianceService } from "@/services/complianceService";
import { ComplianceSummary, ComplianceFlag } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner, DisclaimerBox } from "@/components/ui/DemoBanner";

export default function CompliancePage() {
  const [compliance, setCompliance] = useState<ComplianceSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    complianceService.getComplianceSummary().then((data) => {
      setCompliance(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Statutory Regulatory Compliance Engine"
        subtitle="Automated regulatory rule validation across RESPA, TILA, HMDA LAR, Fair Lending, and Fannie Mae agency selling guidelines."
        breadcrumbs={[
          { label: "Compliance", href: "/compliance" },
        ]}
        demoTag="DEMO RULES ACTIVE"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/risk">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to Risk Assessment
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Statutory Compliance Engine"
        message="Evaluates deterministic regulatory rules. Provides compliance assistance to human underwriters; not legal advice."
      />

      {/* Regulatory Modules Status Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* RESPA */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 uppercase">RESPA</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" /> Passed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            12 CFR § 1026.19 (3-Day LE Delivery & Fee Tolerances)
          </p>
        </div>

        {/* TILA */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 uppercase">TILA / HOEPA</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" /> Passed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            APR / APOR threshold spread: +0.42% (Within safe harbor)
          </p>
        </div>

        {/* HMDA */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 uppercase">HMDA LAR</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" /> Passed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Universal Loan Identifier & Demographic fields validated
          </p>
        </div>

        {/* Fair Lending */}
        <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 uppercase">Fair Lending</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5" /> Passed
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Equal Credit Opportunity Act (ECOA) disparate impact check
          </p>
        </div>

        {/* FNMA / FHLMC */}
        <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-900 uppercase">FNMA Guides</span>
            <span className="inline-flex items-center gap-1 text-[11px] font-mono font-semibold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
              <AlertTriangle className="w-3.5 h-3.5" /> 1 Warning
            </span>
          </div>
          <p className="text-xs text-amber-800 mt-2">
            Asset deposit sourcing condition triggered (B3-4.2-01)
          </p>
        </div>
      </div>

      {/* Compliance Rule Findings Table */}
      <Card
        title="Compliance & Regulatory Rule Audit Log"
        subtitle="Individual rule evaluation results, statutory citations, and required underwriter action items."
      >
        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] tracking-wider border-y border-slate-200">
              <tr>
                <th className="px-6 py-3.5">Regulation</th>
                <th className="px-4 py-3.5">Rule Identifier</th>
                <th className="px-4 py-3.5">Requirement & Citation</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">Observed Input</th>
                <th className="px-6 py-3.5 text-right">Required Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {compliance?.flags.map((flag) => (
                <tr key={flag.id} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-4">
                    <span className="px-2.5 py-1 rounded bg-slate-100 text-slate-800 border border-slate-200 font-mono text-[11px] font-bold">
                      {flag.regulation}
                    </span>
                  </td>
                  <td className="px-4 py-4 font-mono font-bold text-slate-900">
                    {flag.ruleId}
                  </td>
                  <td className="px-4 py-4 max-w-sm">
                    <p className="font-bold text-slate-900">{flag.ruleName}</p>
                    <p className="text-xs text-slate-600 mt-0.5">{flag.description}</p>
                    <p className="text-[11px] text-indigo-700 font-mono font-semibold mt-1">
                      Ref: {flag.citation}
                    </p>
                  </td>
                  <td className="px-4 py-4">
                    {flag.status === "Passed" ? (
                      <span className="inline-flex items-center gap-1.5 text-xs text-emerald-700 font-bold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Passed
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 text-xs text-amber-800 font-bold bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                        <AlertTriangle className="w-3.5 h-3.5" /> Warning Flag
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-4 font-mono text-xs text-slate-700">
                    {flag.triggerDetail}
                  </td>
                  <td className="px-6 py-4 text-right text-xs font-semibold text-slate-800">
                    {flag.recommendedAction}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Mandatory Statutory Disclaimer Box */}
      <DisclaimerBox text="LEGAL DISCLAIMER: This tool delivers compliance assistance and rule verification support. It does not provide definitive legal advice or guarantee automated regulatory indemnification. Human underwriting certification is mandatory prior to loan commitment." />
    </div>
  );
}
