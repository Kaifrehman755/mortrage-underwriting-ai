"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  TrendingDown,
  Sparkles,
  Layers,
  ArrowDown,
} from "lucide-react";
import { riskService } from "@/services/riskService";
import { RiskAssessment } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { ScoreGauge } from "@/components/shared/ScoreGauge";

export default function RiskAssessmentPage() {
  const [risk, setRisk] = useState<RiskAssessment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    riskService.getRiskAssessment().then((data) => {
      setRisk(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Composite Underwriting Risk Assessment"
        subtitle="Transparent multi-factor risk quantification combining deterministic financial ratios, credit depth, collateral strength, and document integrity."
        breadcrumbs={[
          { label: "Risk Assessment", href: "/risk" },
        ]}
        demoTag="DEMO DATA"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/decision">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to AI Recommendation
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Explainable Risk Model"
        message="Transparent causal risk attribution. All factor weights and confidence intervals are computed deterministically."
      />

      {/* Risk Metrics Banner */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visual Risk Gauge */}
        <Card title="Composite Risk Score" subtitle="0 to 100 index (Lower indicates lower default probability).">
          <div className="space-y-4">
            <ScoreGauge
              score={risk?.compositeRiskScore || 24}
              minScore={0}
              maxScore={100}
              label="Composite Risk Index"
              subLabel={`Risk Tier: ${risk?.riskLevel || "LOW"}`}
              type="risk"
            />
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 text-xs space-y-1.5 font-mono">
              <div className="flex justify-between text-slate-600">
                <span>Model Confidence:</span>
                <span className="text-emerald-700 font-bold">{risk?.confidencePercentage || 96}%</span>
              </div>
              <div className="flex justify-between text-slate-600">
                <span>Qualifying Tier:</span>
                <span className="text-slate-900 font-bold">Tier 1 Prime Conforming</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Positive & Compensating Factors */}
        <Card
          title="Mitigating & Compensating Factors"
          subtitle="Identified borrower strengths offsetting underwriting risk."
          className="flex flex-col justify-between"
        >
          <div className="space-y-2.5">
            {risk?.positiveFactors.map((fact, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-xs flex items-start gap-2.5"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-emerald-900">{fact.name}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
                      {fact.metricValue}
                    </span>
                  </div>
                  <p className="text-emerald-800 mt-1 leading-relaxed font-medium">{fact.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Risk & Friction Factors */}
        <Card
          title="Identified Risk Factors"
          subtitle="Areas requiring underwriter scrutiny or document conditioning."
          className="flex flex-col justify-between"
        >
          <div className="space-y-2.5">
            {risk?.riskFactors.map((fact, idx) => (
              <div
                key={idx}
                className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-xs flex items-start gap-2.5"
              >
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-amber-900">{fact.name}</span>
                    <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 border border-amber-300">
                      {fact.metricValue}
                    </span>
                  </div>
                  <p className="text-amber-800 mt-1 leading-relaxed font-medium">{fact.description}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Transparent Explainability Chain */}
      <Card
        title="Explainable Decisioning Lineage"
        subtitle="Deterministic causal mapping from raw extracted input data to composite risk interpretation."
      >
        <div className="space-y-3 pt-2">
          {risk?.explainabilityChain.map((step, idx) => (
            <div
              key={idx}
              className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs font-mono"
            >
              <div className="space-y-1 md:max-w-md">
                <span className="text-indigo-700 font-bold">{step.step}</span>
                <p className="text-slate-900 font-sans font-semibold">{step.input}</p>
                <p className="text-slate-500 text-[11px]">Method: {step.method}</p>
              </div>

              <div className="flex items-center gap-4 shrink-0">
                <div className="text-right">
                  <p className="text-slate-900 font-bold font-sans">{step.output}</p>
                  <p className="text-emerald-700 text-xs font-bold font-mono">{step.riskContribution}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
