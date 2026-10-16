"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User,
  DollarSign,
  Building,
  FolderLock,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { DocumentUploadZone } from "@/components/shared/DocumentUploadZone";
import { applicationService } from "@/services/applicationService";
import {
  Applicant,
  LoanDetails,
  PropertyDetails,
  LoanType,
  PropertyType,
} from "@/types";
import { formatCurrency } from "@/lib/formatters";

const STEPS = [
  { id: 1, name: "1. Applicant", icon: User },
  { id: 2, name: "2. Loan Details", icon: DollarSign },
  { id: 3, name: "3. Property", icon: Building },
  { id: 4, name: "4. Documents", icon: FolderLock },
  { id: 5, name: "5. Review & Submit", icon: CheckCircle2 },
];

export default function NewApplicationPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [createdAppId, setCreatedAppId] = useState<string | null>(null);

  // Form State
  const [applicant, setApplicant] = useState<Applicant>({
    id: "APPL-NEW",
    firstName: "Sarah",
    lastName: "Jenkins",
    email: "sarah.jenkins@example.com",
    phone: "(555) 432-8910",
    ssnMasked: "•••-••-7712",
    dob: "1990-05-18",
    maritalStatus: "Single",
    dependentsCount: 0,
    citizenship: "US_Citizen",
    currentAddress: {
      street: "1420 Pinecrest Terrace",
      city: "Denver",
      state: "CO",
      zipCode: "80202",
      yearsAtAddress: 3.2,
      housingStatus: "Rent",
      monthlyRentMortgage: 2100,
    },
    employment: {
      employerName: "Apex Medical Devices Corp",
      jobTitle: "Lead Biomedical Systems Engineer",
      employmentType: "W2_Employee",
      yearsOnJob: 4.1,
      yearsInProfession: 7,
      monthlyBaseIncome: 11200,
      monthlyBonus: 800,
    },
  });

  const [loan, setLoan] = useState<LoanDetails>({
    loanAmount: 560000,
    purchasePrice: 700000,
    downPayment: 140000,
    downPaymentPercentage: 20.0,
    loanPurpose: "Purchase",
    loanType: "Conventional",
    loanTermMonths: 360,
    interestRate: 6.625,
    rateType: "Fixed",
    amortizationType: "Fixed",
    estimatedMonthlyPayment: {
      principalAndInterest: 3586,
      propertyTaxes: 650,
      hazardInsurance: 175,
      mortgageInsurance: 0,
      hoaFees: 75,
      totalMonthlyPayment: 4486,
    },
  });

  const [property, setProperty] = useState<PropertyDetails>({
    id: "PROP-NEW",
    address: {
      street: "8840 Mountain View Dr",
      city: "Boulder",
      state: "CO",
      zipCode: "80302",
      county: "Boulder",
    },
    propertyType: "Single_Family",
    occupancyType: "Primary_Residence",
    unitsCount: 1,
    yearBuilt: 2018,
    squareFeet: 2650,
    lotSizeAcres: 0.22,
    bedrooms: 3,
    bathrooms: 2.5,
    estimatedAppraisedValue: 715000,
    valuationConfidence: 93,
  });

  const handleNext = () => {
    if (currentStep < 5) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrev = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      const created = await applicationService.createApplication({
        applicant,
        loan,
        property,
      });
      setCreatedAppId(created.id);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Start New Mortgage Loan Application"
        subtitle="Multi-step uniform residential loan application intake wizard (URLA Form 1003 compatible)."
        breadcrumbs={[
          { label: "Applications", href: "/applications" },
          { label: "New Application" },
        ]}
        demoTag="DEMO WIZARD"
      />

      <DemoBanner
        moduleName="Application Intake Engine"
        message="This intake wizard validates inputs locally and initiates the automated extraction and underwriting workflow upon submission."
      />

      {/* Success State */}
      {createdAppId ? (
        <Card className="text-center p-8 space-y-6 border-emerald-300 bg-emerald-50/50 shadow-sm">
          <div className="w-16 h-16 rounded-full bg-emerald-100 border border-emerald-200 flex items-center justify-center text-emerald-600 mx-auto">
            <CheckCircle2 className="w-8 h-8" />
          </div>
          <div>
            <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
              DEMO APPLICATION CREATED
            </span>
            <h2 className="text-2xl font-bold text-slate-900 mt-2">
              Application Initialized: {createdAppId}
            </h2>
            <p className="text-xs text-slate-600 max-w-md mx-auto mt-2 leading-relaxed">
              Loan file created and queued for automated document extraction, deterministic financial calculations, and statutory compliance checks.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
            <Link href={`/applications/${createdAppId}`}>
              <Button variant="primary" size="md" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Open Underwriting Workspace
              </Button>
            </Link>
            <Link href="/applications">
              <Button variant="outline" size="md">
                Back to Applications
              </Button>
            </Link>
          </div>
        </Card>
      ) : (
        <>
          {/* Step Stepper */}
          <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-3 px-6 shadow-xs overflow-x-auto">
            {STEPS.map((step, idx) => {
              const Icon = step.icon;
              const isCurrent = currentStep === step.id;
              const isDone = currentStep > step.id;

              return (
                <React.Fragment key={step.id}>
                  <div
                    className={`flex items-center space-x-2 text-xs font-semibold whitespace-nowrap cursor-pointer select-none ${
                      isCurrent
                        ? "text-slate-950 font-bold"
                        : isDone
                        ? "text-emerald-700"
                        : "text-slate-400"
                    }`}
                    onClick={() => setCurrentStep(step.id)}
                  >
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border font-bold ${
                        isCurrent
                          ? "bg-slate-900 text-white border-slate-900 ring-2 ring-slate-300 shadow-xs"
                          : isDone
                          ? "bg-emerald-100 text-emerald-700 border-emerald-300"
                          : "bg-slate-100 text-slate-500 border-slate-200"
                      }`}
                    >
                      {isDone ? <CheckCircle2 className="w-3.5 h-3.5" /> : step.id}
                    </div>
                    <span className="hidden sm:inline">{step.name}</span>
                  </div>
                  {idx < STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-[2px] mx-2 hidden sm:block ${
                        idx < currentStep - 1 ? "bg-emerald-400" : "bg-slate-200"
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Wizard Step Forms */}
          <Card className="space-y-6">
            {/* Step 1: Applicant */}
            {currentStep === 1 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">
                  1. Borrower Identity & Employment
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      First Name
                    </label>
                    <input
                      type="text"
                      value={applicant.firstName}
                      onChange={(e) => setApplicant({ ...applicant, firstName: e.target.value })}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Last Name
                    </label>
                    <input
                      type="text"
                      value={applicant.lastName}
                      onChange={(e) => setApplicant({ ...applicant, lastName: e.target.value })}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Email Address
                    </label>
                    <input
                      type="email"
                      value={applicant.email}
                      onChange={(e) => setApplicant({ ...applicant, email: e.target.value })}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Phone Number
                    </label>
                    <input
                      type="text"
                      value={applicant.phone}
                      onChange={(e) => setApplicant({ ...applicant, phone: e.target.value })}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Employer Name
                    </label>
                    <input
                      type="text"
                      value={applicant.employment.employerName}
                      onChange={(e) =>
                        setApplicant({
                          ...applicant,
                          employment: { ...applicant.employment, employerName: e.target.value },
                        })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Monthly Base Income ($)
                    </label>
                    <input
                      type="number"
                      value={applicant.employment.monthlyBaseIncome}
                      onChange={(e) =>
                        setApplicant({
                          ...applicant,
                          employment: {
                            ...applicant.employment,
                            monthlyBaseIncome: Number(e.target.value),
                          },
                        })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-semibold focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 2: Loan */}
            {currentStep === 2 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">
                  2. Requested Mortgage Terms
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Purchase Price ($)
                    </label>
                    <input
                      type="number"
                      value={loan.purchasePrice}
                      onChange={(e) => {
                        const price = Number(e.target.value);
                        const down = loan.downPayment;
                        setLoan({
                          ...loan,
                          purchasePrice: price,
                          loanAmount: price - down,
                          downPaymentPercentage: price > 0 ? (down / price) * 100 : 0,
                        });
                      }}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-semibold focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Down Payment ($)
                    </label>
                    <input
                      type="number"
                      value={loan.downPayment}
                      onChange={(e) => {
                        const down = Number(e.target.value);
                        const price = loan.purchasePrice;
                        setLoan({
                          ...loan,
                          downPayment: down,
                          loanAmount: price - down,
                          downPaymentPercentage: price > 0 ? (down / price) * 100 : 0,
                        });
                      }}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-semibold focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Loan Type
                    </label>
                    <select
                      value={loan.loanType}
                      onChange={(e) => setLoan({ ...loan, loanType: e.target.value as LoanType })}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="Conventional">Conventional</option>
                      <option value="FHA">FHA</option>
                      <option value="VA">VA</option>
                      <option value="Jumbo">Jumbo</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Loan Term (Months)
                    </label>
                    <select
                      value={loan.loanTermMonths}
                      onChange={(e) => setLoan({ ...loan, loanTermMonths: Number(e.target.value) })}
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
                    >
                      <option value={360}>30 Years (360 Months)</option>
                      <option value={180}>15 Years (180 Months)</option>
                    </select>
                  </div>
                </div>

                <div className="p-3 bg-indigo-50 border border-indigo-200 rounded-xl text-xs font-mono text-indigo-900 font-bold flex items-center justify-between">
                  <span>Calculated Loan Amount: {formatCurrency(loan.loanAmount)}</span>
                  <span>Equity / Down: {loan.downPaymentPercentage.toFixed(1)}%</span>
                </div>
              </div>
            )}

            {/* Step 3: Property */}
            {currentStep === 3 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">
                  3. Subject Property Information
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="sm:col-span-2">
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Street Address
                    </label>
                    <input
                      type="text"
                      value={property.address.street}
                      onChange={(e) =>
                        setProperty({
                          ...property,
                          address: { ...property.address, street: e.target.value },
                        })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">City</label>
                    <input
                      type="text"
                      value={property.address.city}
                      onChange={(e) =>
                        setProperty({
                          ...property,
                          address: { ...property.address, city: e.target.value },
                        })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">State</label>
                    <input
                      type="text"
                      value={property.address.state}
                      onChange={(e) =>
                        setProperty({
                          ...property,
                          address: { ...property.address, state: e.target.value },
                        })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Property Type
                    </label>
                    <select
                      value={property.propertyType}
                      onChange={(e) =>
                        setProperty({ ...property, propertyType: e.target.value as PropertyType })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-none focus:border-indigo-500"
                    >
                      <option value="Single_Family">Single Family Residence</option>
                      <option value="Condominium">Condominium</option>
                      <option value="Townhouse">Townhouse</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 mb-1">
                      Estimated Appraised Value ($)
                    </label>
                    <input
                      type="number"
                      value={property.estimatedAppraisedValue}
                      onChange={(e) =>
                        setProperty({
                          ...property,
                          estimatedAppraisedValue: Number(e.target.value),
                        })
                      }
                      className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-semibold focus:outline-none focus:border-indigo-500 focus:bg-white"
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Documents */}
            {currentStep === 4 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">
                  4. Attach Initial Documentation
                </h3>
                <DocumentUploadZone />
              </div>
            )}

            {/* Step 5: Review */}
            {currentStep === 5 && (
              <div className="space-y-4">
                <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-2">
                  5. Application Review & Verification
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                    <p className="text-slate-500 font-semibold">Applicant</p>
                    <p className="text-slate-900 font-bold mt-1 text-sm">
                      {applicant.firstName} {applicant.lastName}
                    </p>
                    <p className="text-slate-600 mt-0.5">{applicant.employment.employerName}</p>
                    <p className="text-emerald-700 font-mono font-bold mt-1">
                      {formatCurrency(applicant.employment.monthlyBaseIncome)}/mo
                    </p>
                  </div>

                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                    <p className="text-slate-500 font-semibold">Loan Terms</p>
                    <p className="text-slate-900 font-bold mt-1 font-mono text-sm">
                      {formatCurrency(loan.loanAmount)}
                    </p>
                    <p className="text-slate-600 mt-0.5">
                      {loan.loanType} • {loan.interestRate}%
                    </p>
                    <p className="text-indigo-700 font-mono font-bold mt-1">
                      Down: {formatCurrency(loan.downPayment)} ({loan.downPaymentPercentage.toFixed(1)}%)
                    </p>
                  </div>

                  <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
                    <p className="text-slate-500 font-semibold">Property</p>
                    <p className="text-slate-900 font-bold mt-1 text-sm">{property.address.street}</p>
                    <p className="text-slate-600 mt-0.5">
                      {property.address.city}, {property.address.state}
                    </p>
                    <p className="text-purple-700 font-mono font-bold mt-1">
                      Appraised: {formatCurrency(property.estimatedAppraisedValue)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Step Navigation Controls */}
            <div className="flex items-center justify-between pt-4 border-t border-slate-100">
              <Button
                variant="outline"
                size="sm"
                onClick={handlePrev}
                disabled={currentStep === 1 || submitting}
                leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}
              >
                Previous
              </Button>

              {currentStep < 5 ? (
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleNext}
                  rightIcon={<ArrowRight className="w-3.5 h-3.5" />}
                >
                  Next Step
                </Button>
              ) : (
                <Button
                  variant="success"
                  size="md"
                  onClick={handleSubmit}
                  isLoading={submitting}
                  rightIcon={<CheckCircle2 className="w-4 h-4" />}
                >
                  Create Application (Demo Mode)
                </Button>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
