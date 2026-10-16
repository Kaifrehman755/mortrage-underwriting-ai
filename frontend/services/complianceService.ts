import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { ComplianceSummary } from "@/types";

export const complianceService = {
  async getComplianceSummary(applicationId?: string): Promise<ComplianceSummary> {
    try {
      return await apiClient<ComplianceSummary>(`/compliance?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.complianceSummary : MOCK_APPLICATIONS[0].complianceSummary;
    }
  },
};
