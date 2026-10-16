"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  UploadCloud,
  FileSearch,
  Binary,
  CheckCircle2,
  Cpu,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  AlertOctagon,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";

const PIPELINE_STAGES = [
  {
    step: 1,
    name: "Document Uploaded",
    desc: "Binary payload ingested, SHA-256 hash computed, virus scanned.",
    status: "Completed",
    icon: UploadCloud,
    color: "bg-blue-50 border-blue-200 text-blue-600",
  },
  {
    step: 2,
    name: "Classification",
    desc: "Zero-shot document classification (W-2, 1040, Paystub, Bank Statement).",
    status: "Completed",
    icon: Layers,
    color: "bg-indigo-50 border-indigo-200 text-indigo-600",
  },
  {
    step: 3,
    name: "OCR & Spatial Layout",
    desc: "Multi-modal vision OCR extracting text tokens, key-value pairs, and table grids.",
    status: "Completed",
    icon: Cpu,
    color: "bg-purple-50 border-purple-200 text-purple-600",
  },
  {
    step: 4,
    name: "Data Extraction",
    desc: "Extracting canonical entities (Wages, Taxes, Social Security, Account Balances).",
    status: "Completed",
    icon: FileSearch,
    color: "bg-teal-50 border-teal-200 text-teal-600",
  },
  {
    step: 5,
    name: "Normalization",
    desc: "Formatting date strings, currency values, phone numbers, and address standards.",
    status: "Completed",
    icon: Binary,
    color: "bg-amber-50 border-amber-200 text-amber-600",
  },
  {
    step: 6,
    name: "Cross-Doc Validation",
    desc: "Cross-checking W-2 wages against paystubs and bank deposits for consistency.",
    status: "Completed",
    icon: AlertOctagon,
    color: "bg-rose-50 border-rose-200 text-rose-600",
  },
  {
    step: 7,
    name: "Ready for Analysis",
    desc: "Payload verified and injected into deterministic DTI/LTV calculation engine.",
    status: "Completed",
    icon: ShieldCheck,
    color: "bg-emerald-50 border-emerald-200 text-emerald-600",
  },
];

const PROCESSING_QUEUE = [
  {
    id: "JOB-901",
    fileName: "Vance_W2_2025_ApexCloud.pdf",
    type: "W-2",
    currentStage: "Ready for Analysis",
    progress: 100,
    timeMs: 820,
    confidence: 99.2,
  },
  {
    id: "JOB-902",
    fileName: "Paystub_Vance_Sept2026.pdf",
    type: "Paystub",
    currentStage: "Ready for Analysis",
    progress: 100,
    timeMs: 940,
    confidence: 97.4,
  },
  {
    id: "JOB-903",
    fileName: "BankOfAmerica_Statement_Aug2026.pdf",
    type: "Bank Statement",
    currentStage: "Ready for Analysis",
    progress: 100,
    timeMs: 1450,
    confidence: 95.8,
  },
  {
    id: "JOB-904",
    fileName: "Uniform_Appraisal_Dataset_Report.pdf",
    type: "Appraisal",
    currentStage: "Ready for Analysis",
    progress: 100,
    timeMs: 2100,
    confidence: 96.9,
  },
];

export default function DocumentProcessingPage() {
  const [activeJob, setActiveJob] = useState(PROCESSING_QUEUE[0]);
  const [isSimulating, setIsSimulating] = useState(false);

  const simulateRun = () => {
    setIsSimulating(true);
    setTimeout(() => {
      setIsSimulating(false);
    }, 1200);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Visual Document Processing Pipeline"
        subtitle="End-to-end visual breakdown of the multi-modal OCR ingestion, normalization, and validation lifecycle."
        breadcrumbs={[
          { label: "Document Center", href: "/documents" },
          { label: "Processing Pipeline" },
        ]}
        demoTag="SIMULATION ACTIVE"
        actions={
          <div className="flex items-center space-x-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={simulateRun}
              isLoading={isSimulating}
              leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            >
              Simulate Pipeline Run
            </Button>
            <Link href="/extraction">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Go to Extraction Review
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Visual Processing Engine"
        message="Visual demonstration of asynchronous document OCR steps. Real pipeline will connect to Celery / FastAPI task workers."
      />

      {/* 7-Step Visual Pipeline Stepper */}
      <Card title="Multi-Modal Document Processing Graph" subtitle="Sequential asynchronous transformation stages applied to every uploaded asset.">
        <div className="grid grid-cols-1 md:grid-cols-7 gap-3 pt-2">
          {PIPELINE_STAGES.map((stage) => {
            const Icon = stage.icon;
            return (
              <div
                key={stage.step}
                className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between hover:border-indigo-300 hover:shadow-xs transition relative group"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className={`p-2 rounded-lg border ${stage.color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-mono text-emerald-700 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Ready
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-slate-900 mt-1">{stage.name}</h4>
                  <p className="text-[10px] text-slate-600 mt-1 leading-snug">{stage.desc}</p>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-200 text-[10px] font-mono text-slate-500 font-semibold">
                  Stage {stage.step} of 7
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Live Processing Queue */}
      <Card title="Active Ingestion Queue" subtitle="Real-time execution status and latency metrics for active document files.">
        <div className="space-y-3">
          {PROCESSING_QUEUE.map((job) => (
            <div
              key={job.id}
              className={`p-4 rounded-xl border transition flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer ${
                activeJob.id === job.id
                  ? "bg-indigo-50/50 border-indigo-300 shadow-xs"
                  : "bg-white border-slate-200 hover:border-slate-300"
              }`}
              onClick={() => setActiveJob(job)}
            >
              <div className="flex items-center space-x-3">
                <div className="w-9 h-9 rounded-xl bg-indigo-100 border border-indigo-200 flex items-center justify-center text-indigo-700 shrink-0 font-mono text-xs font-bold">
                  {job.type.slice(0, 3)}
                </div>
                <div>
                  <p className="text-xs font-bold text-slate-900">{job.fileName}</p>
                  <p className="text-[10px] text-slate-500 font-mono">
                    Job ID: {job.id} • Latency: {job.timeMs}ms • Accuracy: {job.confidence}%
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-4">
                <div className="w-32 hidden sm:block">
                  <div className="flex justify-between text-[10px] font-mono text-slate-500 font-semibold mb-1">
                    <span>Progress</span>
                    <span>100%</span>
                  </div>
                  <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-600 rounded-full w-full" />
                  </div>
                </div>

                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 whitespace-nowrap">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  {job.currentStage}
                </span>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
