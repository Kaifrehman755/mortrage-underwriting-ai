import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { UnderwritingReport } from "@/types";

export const reportService = {
  async getUnderwritingReport(applicationId?: string): Promise<UnderwritingReport> {
    try {
      return await apiClient<UnderwritingReport>(`/reports/underwriting?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      const target = app || MOCK_APPLICATIONS[0];

      return {
        applicationId: target.id,
        generatedAt: new Date().toISOString(),
        reportId: `REP-${target.id}-FINAL`,
        applicantSummary: {
          name: `${target.applicant.firstName} ${target.applicant.lastName}`,
          ssnMasked: target.applicant.ssnMasked,
          monthlyIncome: target.financialMetrics.grossMonthlyIncome,
          qualifyingCreditScore: target.creditAnalysis.qualifyingFicoScore,
          employer: target.applicant.employment.employerName,
        },
        loanSummary: {
          amount: target.loan.loanAmount,
          term: `${target.loan.loanTermMonths / 12} Years (${target.loan.rateType})`,
          type: target.loan.loanType,
          rate: `${target.loan.interestRate}%`,
          ltv: target.financialMetrics.ltvPercentage,
          dti: target.financialMetrics.backEndDti,
        },
        propertySummary: {
          address: `${target.property.address.street}, ${target.property.address.city}, ${target.property.address.state}`,
          appraisedValue: target.property.estimatedAppraisedValue,
          valuationConfidence: target.property.valuationConfidence,
        },
        complianceStatus: target.complianceSummary.overallStatus,
        riskLevel: target.riskAssessment.riskLevel,
        riskScore: target.riskAssessment.compositeRiskScore,
        aiRecommendation: target.aiRecommendation.recommendation,
        humanDecision: target.humanReview?.finalDecision,
        reviewerName: target.humanReview?.reviewerName,
        conditionsCount: target.aiRecommendation.stipulationsRequired.length,
        auditTrailEntriesCount: target.auditTrail.length,
      };
    }
  },
};
