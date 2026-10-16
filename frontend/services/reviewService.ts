import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { HumanReview, UnderwriterDecision } from "@/types";

export const reviewService = {
  async submitUnderwriterDecision(
    applicationId: string,
    decision: UnderwriterDecision,
    decisionNotes: string,
    overrideReason?: string,
    approvedLoanAmount?: number,
    approvedInterestRate?: number,
    conditions: string[] = []
  ): Promise<HumanReview> {
    const payload = {
      applicationId,
      reviewerName: "Catherine Hayes, Senior Underwriting Officer",
      reviewerId: "UW-4029",
      reviewedAt: new Date().toISOString(),
      finalDecision: decision,
      overrideOccurred: Boolean(overrideReason && overrideReason.trim() !== ""),
      overrideReason,
      decisionNotes,
      approvedLoanAmount,
      approvedInterestRate,
      conditionsForClosing: conditions,
    };

    try {
      return await apiClient<HumanReview>("/underwriting/review", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } catch {
      // Demo adapter
      const app = MOCK_APPLICATIONS.find((a) => a.id === applicationId) || MOCK_APPLICATIONS[0];
      const review: HumanReview = {
        ...payload,
        aiRecommendation: app.aiRecommendation?.recommendation || "APPROVE",
      };

      app.humanReview = review;
      app.status =
        decision === "Approve"
          ? "Approved"
          : decision === "Deny"
          ? "Denied"
          : decision === "Suspend"
          ? "Suspended"
          : "Needs Review";

      app.auditTrail.unshift({
        id: `AUD-${Date.now()}`,
        applicationId,
        timestamp: new Date().toISOString(),
        actorType: "Underwriter",
        actorName: "Catherine Hayes",
        action: `Human Review Completed: ${decision}`,
        category: "Decision",
        status: decision === "Deny" ? "ALERT" : "SUCCESS",
        details: decisionNotes,
      });

      return review;
    }
  },
};
