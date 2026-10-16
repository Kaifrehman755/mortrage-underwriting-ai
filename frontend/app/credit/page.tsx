"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  CreditCard,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  ArrowRight,
  TrendingDown,
  Building,
  Info,
} from "lucide-react";
import { creditService } from "@/services/creditService";
import { CreditAnalysis } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { ScoreGauge } from "@/components/shared/ScoreGauge";
import { formatCurrency, formatDate } from "@/lib/formatters";

export default function CreditAnalysisPage() {
  const [credit, setCredit] = useState<CreditAnalysis | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    creditService.getCreditAnalysis().then((data) => {
      setCredit(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Tri-Bureau Credit Profile Analysis"
        subtitle="Evaluation of Equifax, Experian, and TransUnion scores, qualifying mid-score determination, revolving utilization, and derogatory tradelines."
        breadcrumbs={[
          { label: "Financial Analysis", href: "/financial" },
          { label: "Credit Analysis" },
        ]}
        demoTag="DEMO DATA"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/property">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to Property Valuation
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Credit Repository Engine"
        message="Displaying tri-merge credit report extract with deterministic qualifying score selection according to Fannie Mae mid-score rules."
      />

      {/* Tri-Bureau Score Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {credit?.bureauScores.map((bureau) => (
          <div key={bureau.bureau} className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm text-center hover:border-slate-300 transition">
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">{bureau.bureau}</span>
            <p className="text-3xl font-extrabold text-slate-900 mt-1 font-mono">{bureau.score}</p>
            <div className="mt-3 pt-2 border-t border-slate-100 text-[11px] text-slate-400 font-mono">
              Pull: {formatDate(bureau.pullDate)} • Ref: {bureau.referenceId}
            </div>
          </div>
        ))}

        {/* Qualifying Score Banner */}
        <div className="p-5 rounded-xl bg-emerald-50 border-2 border-emerald-300 shadow-sm text-center">
          <span className="text-xs text-emerald-800 font-extrabold uppercase tracking-wider">Qualifying Mid-Score</span>
          <p className="text-3xl font-black text-emerald-950 mt-1 font-mono">
            {credit?.qualifyingFicoScore || 760}
          </p>
          <div className="mt-3 pt-2 border-t border-emerald-200 text-xs text-emerald-800 font-semibold font-mono">
            {credit?.scoreTier || "Excellent (740+)"}
          </div>
        </div>
      </div>

      {/* Detailed Credit Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Trade Line Details */}
        <Card
          title="Trade Lines & Revolving Debt Summary"
          subtitle="Aggregated credit limits, active balances, and revolving utilization."
          className="lg:col-span-2"
        >
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 text-xs">
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Open Trade Lines</span>
              <p className="text-lg font-bold text-slate-900 font-mono mt-1">
                {credit?.openTradeLinesCount || 14} Accounts
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Total Credit Limit</span>
              <p className="text-lg font-bold text-slate-900 font-mono mt-1">
                {formatCurrency(credit?.totalCreditLimit || 85000)}
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Total Revolving Balance</span>
              <p className="text-lg font-bold text-slate-900 font-mono mt-1">
                {formatCurrency(credit?.totalBalance || 7800)}
              </p>
            </div>

            <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200">
              <span className="text-emerald-700 font-semibold uppercase tracking-wider text-[10px]">Credit Utilization</span>
              <p className="text-lg font-bold text-emerald-700 font-mono mt-1">
                {credit?.creditUtilizationPercentage || 9.18}%
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Recent Inquiries (6 Mo)</span>
              <p className="text-lg font-bold text-slate-900 font-mono mt-1">
                {credit?.inquiriesLast6Months || 1}
              </p>
            </div>

            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
              <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Collections / Judgments</span>
              <p className="text-lg font-bold text-slate-900 font-mono mt-1">
                {credit?.collectionsCount || 0} ({formatCurrency(credit?.collectionBalanceTotal || 0)})
              </p>
            </div>
          </div>

          {/* Derogatory Marks & Late Payments */}
          <div className="mt-6 pt-4 border-t border-slate-200 space-y-3">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">Delinquency History & Public Records</h4>
            <div className="grid grid-cols-4 gap-3 text-center text-xs">
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 font-mono text-[10px] font-semibold">30-DAY LATES</span>
                <p className="font-bold text-slate-900 font-mono mt-0.5">{credit?.late30DaysCount || 0}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 font-mono text-[10px] font-semibold">60-DAY LATES</span>
                <p className="font-bold text-slate-900 font-mono mt-0.5">{credit?.late60DaysCount || 0}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 font-mono text-[10px] font-semibold">90-DAY LATES</span>
                <p className="font-bold text-slate-900 font-mono mt-0.5">{credit?.late90DaysCount || 0}</p>
              </div>
              <div className="p-3 rounded-lg bg-slate-50 border border-slate-200">
                <span className="text-slate-500 font-mono text-[10px] font-semibold">BANKRUPTCIES</span>
                <p className="font-bold text-slate-900 font-mono mt-0.5">{credit?.bankruptciesCount || 0}</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Visual Gauge Card */}
        <Card title="Credit Tier Standing" subtitle="Tri-bureau representative FICO metric.">
          <div className="space-y-4">
            <ScoreGauge
              score={credit?.qualifyingFicoScore || 760}
              minScore={300}
              maxScore={850}
              label="Qualifying FICO Mid-Score"
              subLabel="Conforming Investor Minimum: 620"
              type="credit"
            />
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs text-slate-600 space-y-1">
              <div className="flex justify-between">
                <span>Prime Tier (740+):</span>
                <span className="text-emerald-700 font-bold">Active</span>
              </div>
              <div className="flex justify-between">
                <span>Pricing Adjustment:</span>
                <span className="text-slate-900 font-medium">0.00% LLPAs</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
