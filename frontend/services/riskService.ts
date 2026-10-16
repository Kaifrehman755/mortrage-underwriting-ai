import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { RiskAssessment } from "@/types";

export const riskService = {
  async getRiskAssessment(applicationId?: string): Promise<RiskAssessment> {
    try {
      return await apiClient<RiskAssessment>(`/underwriting/risk?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.riskAssessment : MOCK_APPLICATIONS[0].riskAssessment;
    }
  },
};
