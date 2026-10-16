"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  UserCheck,
  ArrowRight,
  Info,
  Layers,
  FileCheck2,
} from "lucide-react";
import { decisionService } from "@/services/decisionService";
import { AIRecommendation } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner, DisclaimerBox } from "@/components/ui/DemoBanner";
import { formatDate } from "@/lib/formatters";

export default function AIDecisionPage() {
  const [decision, setDecision] = useState<AIRecommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    decisionService.getAIRecommendation().then((data) => {
      setDecision(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Underwriting Pillar Evaluation &amp; Findings"
        subtitle="Multi-pillar rule assessment synthesizing Capacity, Credit, Collateral, Capital, and Statutory Compliance."
        breadcrumbs={[
          { label: "Pillar Evaluation", href: "/decision" },
        ]}
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/review">
              <Button variant="primary" size="sm" leftIcon={<UserCheck className="w-3.5 h-3.5" />}>
                Proceed to Adjudication Sign-Off
              </Button>
            </Link>
          </div>
        }
      />

      {/* Main Assessment Banner */}
      <div className="p-6 rounded-2xl border border-slate-200 bg-white shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wider">
                SYNTHESIS DISPOSITION
              </span>
              <span className="text-[11px] text-slate-400 font-mono">
                • {decision?.modelIdentifier || "Deterministic Engine v1.0"}
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight flex items-center gap-3">
              <span>{decision?.recommendation || "IN REVIEW"}</span>
              <span className="text-xs font-bold font-mono px-3 py-1 rounded-full bg-slate-100 text-slate-800 border border-slate-200">
                {decision?.confidenceScore || 0}% Verification
              </span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed font-medium">
              {decision?.summary || "Automated synthesis of underwriting criteria across all five financial pillars."}
            </p>
          </div>

          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 text-xs font-mono shrink-0 space-y-1.5">
            <div className="text-slate-600">Generated: <strong className="text-slate-900">{formatDate(decision?.generatedAt)}</strong></div>
            <div className="text-slate-600">Pillars Evaluated: <strong className="text-slate-900">5 of 5</strong></div>
            <div className="text-slate-900 font-bold">Status: Awaiting Underwriter Sign-Off</div>
          </div>
        </div>
      </div>

      {/* 5 Pillars of Underwriting Evaluation */}
      <div>
        <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3">5 Underwriting Pillars Breakdown</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {decision?.pillarBreakdown.map((pillar) => (
            <div key={pillar.pillar} className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-slate-900">{pillar.pillar}</h4>
                  <span
                    className={`inline-flex items-center gap-1 text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                      pillar.status === "Pass"
                        ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                        : "bg-amber-50 text-amber-800 border-amber-300"
                    }`}
                  >
                    {pillar.status === "Pass" ? (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    ) : (
                      <AlertTriangle className="w-3.5 h-3.5" />
                    )}
                    {pillar.status} ({pillar.score}/100)
                  </span>
                </div>
                <p className="text-xs text-slate-600 mt-2.5 leading-relaxed">{pillar.summary}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Stipulations & Closing Conditions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card
          title="Recommended Prior-to-Doc Stipulations"
          subtitle="Conditions that must be satisfied before final loan documents can be issued."
        >
          <ul className="space-y-2.5 text-xs">
            {decision?.stipulationsRequired.map((stip, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-slate-700 font-medium">
                <span className="w-5 h-5 rounded bg-indigo-50 border border-indigo-200 flex items-center justify-center font-mono text-[11px] font-bold text-indigo-700 shrink-0 mt-0.5">
                  {idx + 1}
                </span>
                <span className="leading-relaxed">{stip}</span>
              </li>
            ))}
          </ul>
        </Card>

        <Card
          title="Compensating Factors Identified"
          subtitle="Documented borrower risk mitigants supporting the recommendation."
        >
          <ul className="space-y-2.5 text-xs">
            {decision?.compensatingFactors.map((comp, idx) => (
              <li key={idx} className="flex items-start gap-2.5 text-slate-700 font-medium">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <span className="leading-relaxed">{comp}</span>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <DisclaimerBox text="IMPORTANT NOTICE: The recommendation above represents an automated algorithmic assessment generated by MortgageGuard. Regulatory compliance requires that a human underwriter independently review and approve or modify this decision." />
    </div>
  );
}
