"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  UserCheck,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileQuestion,
  PauseCircle,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Save,
  Check,
  RotateCcw,
} from "lucide-react";
import { reviewService } from "@/services/reviewService";
import { applicationService } from "@/services/applicationService";
import { MortgageApplication, UnderwriterDecision, HumanReview } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner, DisclaimerBox } from "@/components/ui/DemoBanner";
import { formatCurrency } from "@/lib/formatters";

export default function HumanReviewPage() {
  const [app, setApp] = useState<MortgageApplication | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  // Review Form State
  const [selectedDecision, setSelectedDecision] = useState<UnderwriterDecision>("Approve");
  const [decisionNotes, setDecisionNotes] = useState<string>(
    "Approved based on strong 760 qualifying FICO, verified 31.60% DTI, and 20% down payment equity."
  );
  const [overrideReason, setOverrideReason] = useState<string>("");
  const [submittedReview, setSubmittedReview] = useState<HumanReview | null>(null);

  useEffect(() => {
    applicationService.getApplicationById("APP-2026-0841").then((data) => {
      setApp(data);
      if (data?.humanReview) {
        setSubmittedReview(data.humanReview);
        setSelectedDecision(data.humanReview.finalDecision);
        setDecisionNotes(data.humanReview.decisionNotes);
        setOverrideReason(data.humanReview.overrideReason || "");
      }
      setLoading(false);
    });
  }, []);

  const aiRec = app?.aiRecommendation?.recommendation || "APPROVE";
  const isOverride =
    (aiRec === "APPROVE" && (selectedDecision === "Deny" || selectedDecision === "Suspend")) ||
    (aiRec === "DENY" && selectedDecision === "Approve") ||
    selectedDecision === "Override Recommendation";

  const isSubmitDisabled = isOverride && (!overrideReason || overrideReason.trim().length < 10);

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitDisabled) return;

    setSubmitting(true);
    try {
      const review = await reviewService.submitUnderwriterDecision(
        app?.id || "APP-2026-0841",
        selectedDecision,
        decisionNotes,
        isOverride ? overrideReason : undefined,
        app?.loan.loanAmount,
        app?.loan.interestRate,
        app?.aiRecommendation?.stipulationsRequired || []
      );
      setSubmittedReview(review);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Credit Decision & Adjudication Desk"
        subtitle="Underwriter supervisory review, credit decision sign-off, and formal audit logging with condition verification."
        breadcrumbs={[
          { label: "Review Desk", href: "/review" },
        ]}
        demoTag="HUMAN SUPERVISED"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/reports">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Generate Final Underwriting Transmittal
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Human Review Workspace"
        message="Underwriter authority layer. If overriding algorithmic recommendation, a compliant written rationale is mandatory."
      />

      {/* Comparison Header: Rule Synthesis vs Underwriter Final Decision */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Synthesis Side */}
        <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/70 shadow-xs">
          <span className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wider">
            1. Automated Assessment Findings
          </span>
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <span className="text-slate-900">{aiRec}</span>
            </h3>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-slate-200 text-slate-800">
              {app?.aiRecommendation?.confidenceScore || 0}% Score
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-2 leading-relaxed font-medium">
            {app?.aiRecommendation?.summary || "Automated rule evaluation summary pending pipeline execution."}
          </p>
        </div>

        {/* Human Underwriter Side */}
        <div className="p-5 rounded-xl border border-slate-200 bg-slate-50/70 shadow-xs">
          <span className="text-xs font-mono font-bold text-slate-700 uppercase tracking-wider">
            2. Underwriter Adjudication
          </span>
          <div className="flex items-center justify-between mt-2">
            <h3 className="text-2xl font-black text-slate-900 flex items-center gap-2">
              <UserCheck className="w-5 h-5 text-slate-700" />
              <span>{submittedReview ? submittedReview.finalDecision : selectedDecision}</span>
            </h3>
            <span className="text-xs font-mono font-bold px-2.5 py-1 rounded bg-slate-200 text-slate-800">
              {submittedReview ? "Decision Recorded" : "Pending Sign-Off"}
            </span>
          </div>
          <p className="text-xs text-slate-600 mt-2 font-medium">
            Officer: <strong className="text-slate-900">Certified Credit Underwriter</strong>
          </p>
        </div>
      </div>

      {/* Decision Adjudication Workspace Form */}
      <Card title="Underwriter Adjudication Controls" subtitle="Select final disposition and record mandatory audit documentation.">
        <form onSubmit={handleSubmitReview} className="space-y-5">
          {/* Decision Buttons Selector */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2.5">
              Select Final Loan Disposition:
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {[
                { label: "Approve", icon: CheckCircle2, color: "hover:border-emerald-400 hover:bg-emerald-50 text-emerald-800" },
                { label: "Deny", icon: XCircle, color: "hover:border-rose-400 hover:bg-rose-50 text-rose-800" },
                { label: "Request More Documents", icon: FileQuestion, color: "hover:border-blue-400 hover:bg-blue-50 text-blue-800" },
                { label: "Suspend", icon: PauseCircle, color: "hover:border-amber-400 hover:bg-amber-50 text-amber-800" },
                { label: "Override Recommendation", icon: AlertTriangle, color: "hover:border-purple-400 hover:bg-purple-50 text-purple-800" },
              ].map((opt) => {
                const Icon = opt.icon;
                const isSelected = selectedDecision === opt.label;

                return (
                  <button
                    key={opt.label}
                    type="button"
                    onClick={() => setSelectedDecision(opt.label as UnderwriterDecision)}
                    className={`p-3.5 rounded-xl border text-xs font-bold flex flex-col items-center justify-center gap-2 transition ${
                      isSelected
                        ? "bg-indigo-600 text-white border-indigo-600 shadow-md ring-2 ring-indigo-500/30"
                        : `bg-slate-50 text-slate-700 border-slate-200 ${opt.color}`
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{opt.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Override Reason (Required if override is triggered) */}
          {isOverride && (
            <div className="p-4 rounded-xl bg-purple-50 border-2 border-purple-300 space-y-2 animate-in fade-in">
              <div className="flex items-center gap-2 text-purple-900 font-bold text-xs">
                <AlertTriangle className="w-4 h-4 text-purple-700" />
                <span>AI Recommendation Override Reason (MANDATORY FOR AUDIT COMPLIANCE)</span>
              </div>
              <p className="text-xs text-purple-800 font-medium">
                You are deviating from the AI recommendation ({aiRec} vs {selectedDecision}). Detailed supervisory justification is required under CFPB Fair Lending guidelines.
              </p>
              <textarea
                rows={3}
                value={overrideReason}
                onChange={(e) => setOverrideReason(e.target.value)}
                placeholder="Provide comprehensive underwriter justification (minimum 10 characters)..."
                required
                className="w-full bg-white border border-purple-300 rounded-lg p-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
              {overrideReason.trim().length < 10 && (
                <p className="text-xs text-rose-600 font-mono font-bold">
                  * Override rationale must be at least 10 characters before submission.
                </p>
              )}
            </div>
          )}

          {/* Underwriter Decision Notes */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Transmittal Notes & Underwriting Summary:
            </label>
            <textarea
              rows={4}
              value={decisionNotes}
              onChange={(e) => setDecisionNotes(e.target.value)}
              className="w-full bg-white border border-slate-300 rounded-lg p-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
            />
          </div>

          {/* Submit Review Button */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-3 border-t border-slate-200">
            <span className="text-xs text-slate-500 font-mono">
              Action will commit immutable signature to system audit log.
            </span>
            <Button
              type="submit"
              variant={selectedDecision === "Deny" ? "danger" : "success"}
              size="md"
              disabled={isSubmitDisabled || submitting}
              isLoading={submitting}
              leftIcon={<Save className="w-4 h-4" />}
            >
              Sign & Commit Final Decision
            </Button>
          </div>
        </form>
      </Card>

      {/* Confirmation Box if already submitted */}
      {submittedReview && (
        <div className="p-4 bg-emerald-50 border border-emerald-300 rounded-xl flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-3 text-xs text-emerald-900">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
            <div>
              <p className="font-bold">
                Decision Committed: {submittedReview.finalDecision} by {submittedReview.reviewerName}
              </p>
              <p className="text-[11px] text-emerald-700 font-mono mt-0.5">
                Timestamp: {submittedReview.reviewedAt}
              </p>
            </div>
          </div>
          <Link href="/reports">
            <Button variant="secondary" size="sm">
              View Formal Report
            </Button>
          </Link>
        </div>
      )}
    </div>
  );
}
