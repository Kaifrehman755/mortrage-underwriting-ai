import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { PropertyDetails } from "@/types";

export const propertyService = {
  async getPropertyValuation(applicationId?: string): Promise<PropertyDetails> {
    try {
      return await apiClient<PropertyDetails>(`/underwriting/property?application_id=${applicationId || ""}`);
    } catch {
      const app = applicationId
        ? MOCK_APPLICATIONS.find((a) => a.id === applicationId)
        : MOCK_APPLICATIONS[0];
      return app ? app.property : MOCK_APPLICATIONS[0].property;
    }
  },
};
