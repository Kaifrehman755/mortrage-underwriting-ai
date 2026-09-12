import { apiClient } from "@/lib/api";
import { HealthStatusResponse } from "@/types";

export const healthService = {
  async getHealthStatus(): Promise<HealthStatusResponse> {
    return apiClient<HealthStatusResponse>("/health");
  },
};
