import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { CreditAnalysis } from "@/types";

export const creditService = {
  async getCreditAnalysis(applicationId?: string): Promise<CreditAnalysis> {
    try {
      return await apiClient<CreditAnalysis>(`/underwriting/credit?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.creditAnalysis : MOCK_APPLICATIONS[0].creditAnalysis;
    }
  },
};
