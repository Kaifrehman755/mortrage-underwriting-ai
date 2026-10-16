"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Binary,
  Calculator,
  DollarSign,
  TrendingUp,
  Percent,
  Layers,
  ArrowRight,
  ShieldAlert,
  Info,
  RefreshCw,
} from "lucide-react";
import { financialService } from "@/services/financialService";
import { FinancialMetrics } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DemoBanner, DisclaimerBox } from "@/components/ui/DemoBanner";
import { ScoreGauge } from "@/components/shared/ScoreGauge";
import { formatCurrency, formatPercent } from "@/lib/formatters";

export default function FinancialAnalysisPage() {
  const [metrics, setMetrics] = useState<FinancialMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  // Recalculation Form state
  const [grossIncome, setGrossIncome] = useState<number>(21500);
  const [monthlyDebt, setMonthlyDebt] = useState<number>(6793);
  const [loanAmount, setLoanAmount] = useState<number>(640000);
  const [propertyValue, setPropertyValue] = useState<number>(800000);
  const [existingLiens, setExistingLiens] = useState<number>(0);
  const [netOperatingIncome, setNetOperatingIncome] = useState<number>(84000);
  const [annualDebtService, setAnnualDebtService] = useState<number>(67116);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await financialService.getFinancialMetrics();
      setMetrics(data);
      setGrossIncome(data.grossMonthlyIncome);
      setMonthlyDebt(data.totalMonthlyDebt);
      setLoanAmount(data.loanAmount);
      setPropertyValue(data.propertyValue);
      setExistingLiens(data.existingLiensAmount || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRecalculate = async (e: React.FormEvent) => {
    e.preventDefault();
    const updated = await financialService.recalculateFinancials(
      metrics?.applicationId || "APP-2026-0841",
      grossIncome,
      monthlyDebt,
      loanAmount,
      propertyValue,
      existingLiens
    );
    setMetrics(updated);
  };

  const dscrValue =
    annualDebtService > 0 ? (netOperatingIncome / annualDebtService).toFixed(2) : "1.25";

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Deterministic Financial Ratio Analysis"
        subtitle="Mathematical evaluation of Front-End DTI, Back-End DTI, LTV, CLTV, and DSCR conforming to Fannie Mae B3-6 ratio guidelines."
        breadcrumbs={[
          { label: "Financial Analysis", href: "/financial" },
        ]}
        demoTag="DEMO CALCULATION"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/credit">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to Credit Analysis
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Deterministic Calculation Engine v1.0"
        message="Deterministic computation running in demo mode. Results adhere strictly to Fannie Mae Selling Guide formulas without heuristic estimation."
      />

      {/* 4 Core Financial Ratio Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* DTI Card */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-400 transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-600 font-semibold uppercase tracking-wider">Debt-to-Income (DTI)</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1 font-mono">
                {metrics?.backEndDti || 31.6}%
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700">
              <Percent className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-500">
              <span>Gross Income:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(metrics?.grossMonthlyIncome || 21500)}/mo
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Total Debt:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(metrics?.totalMonthlyDebt || 6793)}/mo
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Front-End DTI:</span>
              <span className="font-mono font-bold text-slate-900">
                {metrics?.frontEndDti || 26.01}%
              </span>
            </div>
          </div>
        </div>

        {/* LTV Card */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-400 transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-600 font-semibold uppercase tracking-wider">Loan-to-Value (LTV)</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1 font-mono">
                {metrics?.ltvPercentage || 80.0}%
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-800">
              <DollarSign className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-500">
              <span>Loan Amount:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(metrics?.loanAmount || 640000)}
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Property Value:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(metrics?.propertyValue || 800000)}
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Equity / Down:</span>
              <span className="font-mono font-bold text-emerald-600">
                {formatPercent(100 - (metrics?.ltvPercentage || 80.0), 1)}
              </span>
            </div>
          </div>
        </div>

        {/* CLTV Card */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-400 transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-slate-600 font-semibold uppercase tracking-wider">Combined LTV (CLTV)</p>
              <h3 className="text-3xl font-extrabold text-slate-900 mt-1 font-mono">
                {metrics?.cltvPercentage || 80.0}%
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-100 border border-slate-200 text-slate-800">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-500">
              <span>1st Lien Amount:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(metrics?.loanAmount || 640000)}
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Subordinate Liens:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(metrics?.existingLiensAmount || 0)}
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Total Encumbrance:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency((metrics?.loanAmount || 640000) + (metrics?.existingLiensAmount || 0))}
              </span>
            </div>
          </div>
        </div>

        {/* DSCR Card */}
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-emerald-300 transition">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-xs text-emerald-700 font-semibold uppercase tracking-wider">Debt Service Coverage (DSCR)</p>
              <h3 className="text-3xl font-extrabold text-emerald-600 mt-1 font-mono">
                {dscrValue}x
              </h3>
            </div>
            <div className="p-2.5 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-600">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-100 space-y-1.5 text-xs">
            <div className="flex justify-between text-slate-500">
              <span>Annual NOI:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(netOperatingIncome)}
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Annual Debt Service:</span>
              <span className="font-mono font-bold text-slate-900">
                {formatCurrency(annualDebtService)}
              </span>
            </div>
            <div className="flex justify-between text-slate-500">
              <span>Investor Standard:</span>
              <span className="font-mono font-bold text-emerald-600">1.20x Min</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recalculation Form & Deterministic Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recalculation Simulator */}
        <Card
          title="Ratio Recalculation Simulator"
          subtitle="Simulate debt payoff or down payment modifications to observe deterministic ratio impact."
          className="lg:col-span-2"
        >
          <form onSubmit={handleRecalculate} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Gross Monthly Income ($)
                </label>
                <input
                  type="number"
                  value={grossIncome}
                  onChange={(e) => setGrossIncome(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 font-mono shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Total Monthly Debt Obligations ($)
                </label>
                <input
                  type="number"
                  value={monthlyDebt}
                  onChange={(e) => setMonthlyDebt(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 font-mono shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Requested Loan Amount ($)
                </label>
                <input
                  type="number"
                  value={loanAmount}
                  onChange={(e) => setLoanAmount(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 font-mono shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
                  Appraised Property Value ($)
                </label>
                <input
                  type="number"
                  value={propertyValue}
                  onChange={(e) => setPropertyValue(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3.5 py-2.5 text-sm text-slate-900 font-mono shadow-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-4 border-t border-slate-200">
              <span className="text-xs font-mono text-slate-500">
                Formula: DTI = (Debt / Income) × 100 • LTV = (Loan / Value) × 100
              </span>
              <Button variant="primary" size="sm" type="submit" leftIcon={<Calculator className="w-4 h-4" />}>
                Execute Recalculation
              </Button>
            </div>
          </form>
        </Card>

        {/* Visual Ratio Gauge */}
        <Card title="DTI & Equity Health" subtitle="Visual ratio positioning against investor limits.">
          <div className="space-y-4">
            <ScoreGauge
              score={metrics?.backEndDti || 31.6}
              minScore={0}
              maxScore={60}
              label="Back-End DTI Ratio"
              subLabel="Fannie Mae 45.0% Standard Ceiling"
              type="dti"
            />
            <DisclaimerBox text="The calculation engine calculates deterministic values. Threshold acceptance is evaluated by the compliance & risk rulesets." />
          </div>
        </Card>
      </div>
    </div>
  );
}
