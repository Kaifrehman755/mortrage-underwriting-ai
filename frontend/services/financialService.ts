import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { FinancialMetrics } from "@/types";

export const financialService = {
  async getFinancialMetrics(applicationId?: string): Promise<FinancialMetrics> {
    try {
      return await apiClient<FinancialMetrics>(`/underwriting/financial?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.financialMetrics : MOCK_APPLICATIONS[0].financialMetrics;
    }
  },

  async recalculateFinancials(
    applicationId: string,
    grossIncome: number,
    totalMonthlyDebt: number,
    loanAmount: number,
    propertyValue: number,
    existingLiens = 0
  ): Promise<FinancialMetrics> {
    try {
      return await apiClient<FinancialMetrics>("/underwriting/calculate", {
        method: "POST",
        body: JSON.stringify({
          applicationId,
          grossIncome,
          totalMonthlyDebt,
          loanAmount,
          propertyValue,
          existingLiens,
        }),
      });
    } catch {
      // Deterministic demo computation reflecting backend calculation formula
      const frontEndDti = grossIncome > 0 ? (totalMonthlyDebt * 0.8 / grossIncome) * 100 : 0;
      const backEndDti = grossIncome > 0 ? (totalMonthlyDebt / grossIncome) * 100 : 0;
      const ltvPercentage = propertyValue > 0 ? (loanAmount / propertyValue) * 100 : 0;
      const cltvPercentage = propertyValue > 0 ? ((loanAmount + existingLiens) / propertyValue) * 100 : 0;

      const updatedMetrics: FinancialMetrics = {
        applicationId,
        grossMonthlyIncome: grossIncome,
        totalMonthlyDebt,
        frontEndDti: Number(frontEndDti.toFixed(2)),
        backEndDti: Number(backEndDti.toFixed(2)),
        loanAmount,
        propertyValue,
        ltvPercentage: Number(ltvPercentage.toFixed(2)),
        existingLiensAmount: existingLiens,
        cltvPercentage: Number(cltvPercentage.toFixed(2)),
        liquidAssetsTotal: 214830,
        reservesMonths: 9.8,
        calculationStatus: "Calculated",
        warnings: [],
        calculationEngine: "Deterministic Engine v1.0 (Demo)",
      };

      const app = MOCK_APPLICATIONS.find((a) => a.id === applicationId);
      if (app) {
        app.financialMetrics = updatedMetrics;
      }

      return updatedMetrics;
    }
  },
};
