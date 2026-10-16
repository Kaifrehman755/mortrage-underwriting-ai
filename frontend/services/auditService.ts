import { apiClient } from "@/lib/api";
import { MOCK_AUDIT_LOGS, MOCK_APPLICATIONS } from "@/lib/mockData";
import { AuditEvent } from "@/types";

export const auditService = {
  async getAuditTrail(applicationId?: string): Promise<AuditEvent[]> {
    try {
      return await apiClient<AuditEvent[]>(`/audit?application_id=${applicationId || ""}`);
    } catch {
      if (applicationId) {
        const app = MOCK_APPLICATIONS.find((a) => a.id === applicationId);
        if (app && app.auditTrail.length > 0) {
          return app.auditTrail;
        }
      }
      return MOCK_AUDIT_LOGS;
    }
  },
};
