import { apiClient } from "@/lib/api";
import { MOCK_APPLICATIONS } from "@/lib/mockData";
import { MortgageApplication, DashboardStats, ApplicationStatus, RiskLevel } from "@/types";

export interface ApplicationFilterParams {
  status?: ApplicationStatus | "All";
  riskLevel?: RiskLevel | "All";
  searchQuery?: string;
}

export const applicationService = {
  /**
   * Fetch summary dashboard metrics
   */
  async getDashboardStats(): Promise<DashboardStats> {
    try {
      return await apiClient<DashboardStats>("/applications/dashboard");
    } catch {
      // Return clean zeroed metrics when backend is not connected
      return {
        activeApplicationsCount: 0,
        pendingReviewCount: 0,
        documentsProcessingCount: 0,
        highRiskCasesCount: 0,
        averageTurnaroundHours: 0,
        straightThroughProcessingRate: 0,
        recentApplications: [],
      };
    }
  },

  /**
   * Fetch all applications with filtering
   * Returns empty array if backend is not linked or has no data
   */
  async getApplications(params?: ApplicationFilterParams): Promise<MortgageApplication[]> {
    try {
      const data = await apiClient<MortgageApplication[]>("/applications");
      let results = data || [];

      if (params?.status && params.status !== "All") {
        results = results.filter((app) => app.status === params.status);
      }
      if (params?.riskLevel && params.riskLevel !== "All") {
        results = results.filter((app) => app.riskLevel === params.riskLevel);
      }
      if (params?.searchQuery && params.searchQuery.trim() !== "") {
        const q = params.searchQuery.toLowerCase().trim();
        results = results.filter(
          (app) =>
            app.id.toLowerCase().includes(q) ||
            app.applicationNumber.toLowerCase().includes(q) ||
            `${app.applicant?.firstName} ${app.applicant?.lastName}`.toLowerCase().includes(q) ||
            app.property?.address?.street?.toLowerCase().includes(q)
        );
      }

      return results;
    } catch {
      // Rule: Do NOT inject mock data if there is no data; return clean empty array
      return [];
    }
  },

  /**
   * Fetch single application by ID
   */
  async getApplicationById(id: string): Promise<MortgageApplication | null> {
    try {
      return await apiClient<MortgageApplication>(`/applications/${id}`);
    } catch {
      return null;
    }
  },

  /**
   * Get an optional realistic sandbox template for standalone testing
   */
  getSandboxTemplate(): MortgageApplication {
    return MOCK_APPLICATIONS[0];
  },

  /**
   * Create a new mortgage application (Multi-step wizard)
   */
  async createApplication(payload: Partial<MortgageApplication>): Promise<MortgageApplication> {
    try {
      return await apiClient<MortgageApplication>("/applications", {
        method: "POST",
        body: JSON.stringify(payload),
      });
    } catch {
      // Demo adapter: generate realistic new application record
      const newId = `APP-2026-${Math.floor(1000 + Math.random() * 9000)}`;
      const newApp: MortgageApplication = {
        id: newId,
        applicationNumber: `LN-${newId}`,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        status: "Draft",
        riskLevel: "MODERATE",
        isDemoData: true,
        applicant: payload.applicant || MOCK_APPLICATIONS[0].applicant,
        coApplicant: payload.coApplicant,
        loan: payload.loan || MOCK_APPLICATIONS[0].loan,
        property: payload.property || MOCK_APPLICATIONS[0].property,
        documents: [],
        extractedFields: [],
        validationIssues: [],
        financialMetrics: {
          ...MOCK_APPLICATIONS[0].financialMetrics,
          applicationId: newId,
        },
        creditAnalysis: {
          ...MOCK_APPLICATIONS[0].creditAnalysis,
          applicationId: newId,
        },
        complianceSummary: {
          ...MOCK_APPLICATIONS[0].complianceSummary,
          applicationId: newId,
        },
        riskAssessment: {
          ...MOCK_APPLICATIONS[0].riskAssessment,
          applicationId: newId,
        },
        aiRecommendation: {
          ...MOCK_APPLICATIONS[0].aiRecommendation,
          applicationId: newId,
        },
        auditTrail: [
          {
            id: `AUD-${Date.now()}`,
            applicationId: newId,
            timestamp: new Date().toISOString(),
            actorType: "Underwriter",
            actorName: "Current User",
            action: "Application Created (Demo Mode)",
            category: "Creation",
            status: "SUCCESS",
            details: "Application initialized via multi-step wizard.",
          },
        ],
      };

      MOCK_APPLICATIONS.unshift(newApp);
      return newApp;
    }
  },
};
