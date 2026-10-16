import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { AIRecommendation } from "@/types";

export const decisionService = {
  async getAIRecommendation(applicationId?: string): Promise<AIRecommendation> {
    try {
      return await apiClient<AIRecommendation>(`/underwriting/decision?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.aiRecommendation : MOCK_APPLICATIONS[0].aiRecommendation;
    }
  },
};
