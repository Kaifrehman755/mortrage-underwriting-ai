# Regulatory Compliance Framework

> **Current Status**: **Phase 0 Module Setup**. Compliance evaluation rules are mapped to statutory standards and planned for programmatic and RAG-assisted validation.

---

## 1. Regulatory Scope & Statutes

The mortgage underwriting system will enforce compliance across major US mortgage lending regulations:

### 1.1 Fannie Mae (FNMA) & Freddie Mac (FHLMC) Conforming Guidelines
- Maximum Debt-to-Income (DTI) ratio thresholds (typically 45-50% with Desktop Underwriter / Loan Product Advisor compensating factors).
- Loan-to-Value (LTV) limits and Private Mortgage Insurance (PMI) triggers.
- Reserve requirements based on loan type and occupancy.

### 1.2 Truth in Lending Act (TILA / Regulation Z) & TRID
- Integrated Disclosure rule (Loan Estimate & Closing Disclosure timing).
- Annual Percentage Rate (APR) vs. Average Prime Offer Rate (APOR) spread calculations.
- Qualified Mortgage (QM) / Ability-to-Repay (ATR) standard enforcement.

### 1.3 Real Estate Settlement Procedures Act (RESPA / Regulation X)
- Timely delivery of initial disclosures (within 3 business days of application).
- Section 8 prohibition against kickbacks and unearned fees.

### 1.4 Home Mortgage Disclosure Act (HMDA / Regulation C)
- Comprehensive Loan Application Register (LAR) data validation.
- Rate spread, credit score, action taken, and denial reason tracking.

### 1.5 Equal Credit Opportunity Act (ECOA / Regulation B) & Fair Housing Act
- Adverse action notice requirements (30 days from complete application).
- Disparate impact and prohibited basis discrimination detection.

---

## 2. Enforcement Methodology

```text
Application Data
       │
       ├───► [1] Deterministic Rules Engine (TILA/RESPA/HMDA hard boundary checks)
       │
       └───► [2] RAG Guideline Engine (FNMA/FHLMC selling guide contextual retrieval)
       │
       ▼
Compliance Audit Report (Pass / Fail / Flags / Mitigating Conditions)
```
