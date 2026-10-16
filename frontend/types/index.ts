export type ApplicationStatus =
  | "Draft"
  | "Processing"
  | "Needs Review"
  | "Approved"
  | "Denied"
  | "Suspended";

export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "CRITICAL";

export type LoanPurpose = "Purchase" | "Refinance_RateTerm" | "Refinance_CashOut" | "Construction";
export type LoanType = "Conventional" | "FHA" | "VA" | "USDA" | "Jumbo";
export type PropertyType = "Single_Family" | "Condominium" | "Townhouse" | "Multi_Family_2_4" | "Commercial";
export type OccupancyType = "Primary_Residence" | "Secondary_Home" | "Investment";
export type EmploymentType = "W2_Employee" | "Self_Employed" | "Retired" | "Other";

export type DocumentType =
  | "W-2"
  | "1040"
  | "Paystub"
  | "Bank Statement"
  | "Credit Report"
  | "Appraisal"
  | "Purchase Agreement"
  | "Title Insurance"
  | "Other";

export type DocumentProcessingStatus =
  | "Uploaded"
  | "Classifying"
  | "OCR_Processing"
  | "Extracting"
  | "Normalized"
  | "Validated"
  | "Failed";

export type ValidationSeverity = "INFO" | "WARNING" | "CRITICAL";

export type ValidationCategory =
  | "Missing Documents"
  | "Contradictions"
  | "Invalid Values"
  | "Low OCR Confidence"
  | "Duplicate Documents"
  | "Expired Documents"
  | "Calculation Issues";

export type AIRecommendationDecision = "APPROVE" | "DENY" | "SUSPEND / HUMAN REVIEW";
export type UnderwriterDecision = "Approve" | "Deny" | "Request More Documents" | "Suspend" | "Override Recommendation";

// Health & System
export interface HealthStatusResponse {
  status: "healthy" | "unhealthy" | "degraded" | string;
  service: string;
  version: string;
  environment: string;
  database: string;
}

export interface NavigationItem {
  name: string;
  href: string;
  icon: string;
  badge?: string;
  active?: boolean;
}

// Applicant
export interface Applicant {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  ssnMasked: string;
  dob: string;
  maritalStatus: "Single" | "Married" | "Separated" | "Unmarried";
  dependentsCount: number;
  citizenship: "US_Citizen" | "Permanent_Resident" | "Non_Permanent_Resident";
  currentAddress: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    yearsAtAddress: number;
    housingStatus: "Own" | "Rent" | "Other";
    monthlyRentMortgage?: number;
  };
  employment: {
    employerName: string;
    jobTitle: string;
    employmentType: EmploymentType;
    yearsOnJob: number;
    yearsInProfession: number;
    monthlyBaseIncome: number;
    monthlyOvertime?: number;
    monthlyBonus?: number;
    monthlyOtherIncome?: number;
    employerAddress?: string;
    employerPhone?: string;
  };
}

// Co-Applicant
export interface CoApplicant extends Applicant {
  relationshipToPrimary: "Spouse" | "Co-Borrower" | "Other";
}

// Loan Details
export interface LoanDetails {
  loanAmount: number;
  purchasePrice: number;
  downPayment: number;
  downPaymentPercentage: number;
  loanPurpose: LoanPurpose;
  loanType: LoanType;
  loanTermMonths: number; // e.g., 360 for 30yr
  interestRate: number; // percentage, e.g. 6.75
  rateType: "Fixed" | "ARM";
  amortizationType: "Fixed" | "Adjustable";
  estimatedMonthlyPayment: {
    principalAndInterest: number;
    propertyTaxes: number;
    hazardInsurance: number;
    mortgageInsurance: number;
    hoaFees: number;
    totalMonthlyPayment: number;
  };
}

// Property Details
export interface PropertyDetails {
  id: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    county: string;
  };
  propertyType: PropertyType;
  occupancyType: OccupancyType;
  unitsCount: number;
  yearBuilt: number;
  squareFeet: number;
  lotSizeAcres?: number;
  bedrooms: number;
  bathrooms: number;
  parcelNumber?: string;
  estimatedAppraisedValue: number;
  appraisalDate?: string;
  appraiserName?: string;
  valuationConfidence: number; // 0-100%
  comparables?: PropertyComparable[];
}

export interface PropertyComparable {
  id: string;
  address: string;
  salePrice: number;
  saleDate: string;
  squareFeet: number;
  pricePerSqFt: number;
  distanceMiles: number;
  bedrooms: number;
  bathrooms: number;
  netAdjustment: number;
  adjustedValue: number;
}

// Document Management
export interface UnderwritingDocument {
  id: string;
  applicationId: string;
  fileName: string;
  fileSize: number; // in bytes
  fileType: string;
  documentType: DocumentType;
  uploadedAt: string;
  processingStatus: DocumentProcessingStatus;
  ocrConfidence: number; // 0-100
  extractedFieldCount: number;
  validationIssueCount: number;
  fileUrl?: string;
  sha256Hash: string;
}

// Extracted Data Field
export interface ExtractedField {
  id: string;
  documentId: string;
  documentName: string;
  category: "Applicant" | "Income" | "Asset" | "Liability" | "Property" | "Tax";
  fieldName: string;
  rawExtractedValue: string;
  normalizedValue: string | number;
  confidence: number; // 0-100
  sourcePage: number;
  boundingBox?: { x: number; y: number; width: number; height: number };
  validationStatus: "Verified" | "Flagged" | "Edited" | "Pending";
  underwriterNote?: string;
}

// Validation Issue
export interface ValidationIssue {
  id: string;
  applicationId: string;
  category: ValidationCategory;
  severity: ValidationSeverity;
  title: string;
  description: string;
  sourceDocuments: string[];
  affectedFields: string[];
  detectedAt: string;
  status: "Open" | "Acknowledged" | "Resolved" | "Waived";
  resolutionNote?: string;
}

// Financial Metrics
export interface FinancialMetrics {
  applicationId: string;
  grossMonthlyIncome: number;
  totalMonthlyDebt: number;
  frontEndDti: number; // Housing DTI %
  backEndDti: number; // Total DTI %
  loanAmount: number;
  propertyValue: number;
  ltvPercentage: number;
  existingLiensAmount: number;
  cltvPercentage: number;
  liquidAssetsTotal: number;
  reservesMonths: number;
  netOperatingIncome?: number;
  annualDebtService?: number;
  dscrRatio?: number;
  calculationStatus: "Calculated" | "Pending_Input" | "Invalid";
  warnings: string[];
  calculationEngine: "Deterministic Engine v1.0 (Demo)";
}

// Credit Profile & Analysis
export interface CreditBureauScore {
  bureau: "Equifax" | "Experian" | "TransUnion";
  score: number;
  pullDate: string;
  referenceId: string;
}

export interface CreditAnalysis {
  applicationId: string;
  bureauScores: CreditBureauScore[];
  qualifyingFicoScore: number; // Mid-score rule
  scoreTier: "Excellent (740+)" | "Good (680-739)" | "Fair (620-679)" | "Subprime (<620)";
  openTradeLinesCount: number;
  totalCreditLimit: number;
  totalBalance: number;
  creditUtilizationPercentage: number;
  derogatoryMarksCount: number;
  late30DaysCount: number;
  late60DaysCount: number;
  late90DaysCount: number;
  collectionsCount: number;
  collectionBalanceTotal: number;
  bankruptciesCount: number;
  foreclosuresCount: number;
  inquiriesLast6Months: number;
  flags: string[];
  missingInformation: string[];
}

// Compliance Results
export interface ComplianceFlag {
  id: string;
  ruleId: string;
  regulation: "RESPA" | "TILA" | "HMDA" | "Fair Lending" | "FNMA_FHLMC";
  ruleName: string;
  description: string;
  severity: "INFO" | "WARNING" | "CRITICAL";
  status: "Passed" | "Warning" | "Flagged" | "Needs Human Review";
  citation: string;
  triggerDetail: string;
  recommendedAction: string;
}

export interface ComplianceSummary {
  applicationId: string;
  overallStatus: "Passed" | "Warning" | "Flagged" | "Needs Human Review";
  regulationsEvaluated: {
    respa: "Passed" | "Warning" | "Flagged";
    tila: "Passed" | "Warning" | "Flagged";
    hmda: "Passed" | "Warning" | "Flagged";
    fairLending: "Passed" | "Warning" | "Flagged";
    fnmaGuidelines: "Passed" | "Warning" | "Flagged";
  };
  totalRulesEvaluated: number;
  passedCount: number;
  warningCount: number;
  flaggedCount: number;
  flags: ComplianceFlag[];
  disclaimer: "Compliance Assistance tool only. Does not constitute binding statutory legal advice. Human underwriter review mandatory.";
}

// Risk Assessment
export interface RiskFactor {
  category: "Financial" | "Credit" | "Property" | "Documentation" | "Compliance" | "Income";
  type: "Negative" | "Positive" | "Neutral";
  name: string;
  impactWeight: "Low" | "Medium" | "High";
  description: string;
  metricValue: string;
}

export interface RiskAssessment {
  applicationId: string;
  compositeRiskScore: number; // 0 to 100
  riskLevel: RiskLevel;
  confidencePercentage: number;
  riskFactors: RiskFactor[];
  positiveFactors: RiskFactor[];
  explainabilityChain: {
    step: string;
    input: string;
    method: string;
    output: string;
    riskContribution: string;
  }[];
}

// AI Recommendation
export interface AIRecommendation {
  applicationId: string;
  recommendation: AIRecommendationDecision;
  confidenceScore: number; // 0 - 100
  generatedAt: string;
  modelIdentifier: "MortgageGuard-LLM-v2.4 (Explainable)";
  summary: string;
  pillarBreakdown: {
    pillar: string;
    status: "Pass" | "Caution" | "Fail";
    score: number;
    summary: string;
  }[];
  stipulationsRequired: string[];
  compensatingFactors: string[];
}

// Human Review & Final Decision
export interface HumanReview {
  applicationId: string;
  reviewerName: string;
  reviewerId: string;
  reviewedAt: string;
  aiRecommendation: AIRecommendationDecision;
  finalDecision: UnderwriterDecision;
  overrideOccurred: boolean;
  overrideReason?: string;
  decisionNotes: string;
  approvedLoanAmount?: number;
  approvedInterestRate?: number;
  conditionsForClosing: string[];
}

// Audit Trail Event
export interface AuditEvent {
  id: string;
  applicationId: string;
  timestamp: string;
  actorType: "System" | "AI Agent" | "Underwriter" | "Loan Officer" | "Compliance Engine";
  actorName: string;
  action: string;
  category: "Creation" | "Document" | "Extraction" | "Calculation" | "Compliance" | "Risk" | "Decision" | "Override";
  status: "SUCCESS" | "WARNING" | "ALERT" | "INFO";
  details: string;
  metadata?: Record<string, string | number | boolean>;
  hash?: string;
}

// Complete Mortgage Application Entity
export interface MortgageApplication {
  id: string;
  applicationNumber: string;
  createdAt: string;
  updatedAt: string;
  status: ApplicationStatus;
  riskLevel: RiskLevel;
  applicant: Applicant;
  coApplicant?: CoApplicant;
  loan: LoanDetails;
  property: PropertyDetails;
  documents: UnderwritingDocument[];
  extractedFields: ExtractedField[];
  validationIssues: ValidationIssue[];
  financialMetrics: FinancialMetrics;
  creditAnalysis: CreditAnalysis;
  complianceSummary: ComplianceSummary;
  riskAssessment: RiskAssessment;
  aiRecommendation: AIRecommendation;
  humanReview?: HumanReview;
  auditTrail: AuditEvent[];
  isDemoData: boolean;
}

// Dashboard Summary Stats
export interface DashboardStats {
  activeApplicationsCount: number;
  pendingReviewCount: number;
  documentsProcessingCount: number;
  highRiskCasesCount: number;
  averageTurnaroundHours: number;
  straightThroughProcessingRate: number;
  recentApplications: MortgageApplication[];
}

// Underwriting Report Summary
export interface UnderwritingReport {
  applicationId: string;
  generatedAt: string;
  reportId: string;
  applicantSummary: {
    name: string;
    ssnMasked: string;
    monthlyIncome: number;
    qualifyingCreditScore: number;
    employer: string;
  };
  loanSummary: {
    amount: number;
    term: string;
    type: string;
    rate: string;
    ltv: number;
    dti: number;
  };
  propertySummary: {
    address: string;
    appraisedValue: number;
    valuationConfidence: number;
  };
  complianceStatus: string;
  riskLevel: RiskLevel;
  riskScore: number;
  aiRecommendation: AIRecommendationDecision;
  humanDecision?: UnderwriterDecision;
  reviewerName?: string;
  conditionsCount: number;
  auditTrailEntriesCount: number;
}
