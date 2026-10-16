"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderLock,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Eye,
  Filter,
  FileCheck2,
  Cpu,
} from "lucide-react";
import { documentService } from "@/services/documentService";
import { UnderwritingDocument, DocumentType } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { DocumentUploadZone } from "@/components/shared/DocumentUploadZone";
import { formatDate, formatFileSize } from "@/lib/formatters";

const DOC_CATEGORIES: (DocumentType | "All")[] = [
  "All",
  "W-2",
  "1040",
  "Paystub",
  "Bank Statement",
  "Credit Report",
  "Appraisal",
  "Purchase Agreement",
];

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<UnderwritingDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState<DocumentType | "All">("All");
  const [previewDoc, setPreviewDoc] = useState<UnderwritingDocument | null>(null);

  const loadDocs = async () => {
    setLoading(true);
    try {
      const data = await documentService.getAllDocuments();
      setDocuments(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDocs();
  }, []);

  const filteredDocs =
    categoryFilter === "All"
      ? documents
      : documents.filter((d) => d.documentType === categoryFilter);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Document Ingestion & Management Center"
        subtitle="Multi-modal document intake, automated classification, OCR extraction, and tamper-evident SHA-256 integrity verification."
        breadcrumbs={[{ label: "Document Center", href: "/documents" }]}
        demoTag="DEMO DATA"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/processing">
              <Button variant="secondary" size="sm" leftIcon={<Cpu className="w-3.5 h-3.5" />}>
                View Processing Pipeline
              </Button>
            </Link>
            <Link href="/extraction">
              <Button variant="primary" size="sm" leftIcon={<FileCheck2 className="w-3.5 h-3.5" />}>
                Review Extracted Fields
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Document Intelligence Engine"
        message="Displaying sample ingested loan documents. All OCR confidence scores and extracted field counts are deterministically synthesized."
      />

      {/* Upload Zone Component */}
      <DocumentUploadZone onUploadComplete={loadDocs} />

      {/* Filter Toolbar */}
      <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-3 px-4 shadow-xs">
        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-xs text-slate-700 font-semibold">Filter by Type:</span>
          <div className="flex flex-wrap gap-1.5">
            {DOC_CATEGORIES.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded-lg text-xs transition font-semibold ${
                  categoryFilter === cat
                    ? "bg-slate-900 text-white shadow-xs"
                    : "bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200"
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>

        <span className="text-xs text-slate-500 font-mono font-medium hidden sm:inline">
          {filteredDocs.length} Total Documents
        </span>
      </div>

      {/* Document List Table */}
      <Card className="p-0 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] tracking-wider border-b border-slate-200 font-bold">
              <tr>
                <th className="px-6 py-3.5">Document Name</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Uploaded</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-4 py-3.5">OCR Confidence</th>
                <th className="px-4 py-3.5">Extracted Fields</th>
                <th className="px-4 py-3.5">Validation Issues</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {filteredDocs.map((doc) => (
                <tr key={doc.id} className="hover:bg-indigo-50/40 transition">
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-indigo-50 border border-indigo-200 text-indigo-600">
                        <FileText className="w-4 h-4" />
                      </div>
                      <div>
                        <p className="font-bold text-slate-900 hover:text-indigo-600 hover:underline cursor-pointer" onClick={() => setPreviewDoc(doc)}>
                          {doc.fileName}
                        </p>
                        <p className="text-[10px] text-slate-500 font-mono">
                          {formatFileSize(doc.fileSize)} • SHA: {doc.sha256Hash.slice(0, 10)}...
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 font-mono text-[11px] font-semibold">
                      {doc.documentType}
                    </span>
                  </td>
                  <td className="px-4 py-4 text-slate-500 text-[11px] font-mono">
                    {formatDate(doc.uploadedAt)}
                  </td>
                  <td className="px-4 py-4">
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="w-3 h-3" />
                      {doc.processingStatus}
                    </span>
                  </td>
                  <td className="px-4 py-4 font-mono font-bold">
                    <span
                      className={
                        doc.ocrConfidence >= 95
                          ? "text-emerald-700"
                          : doc.ocrConfidence >= 90
                          ? "text-blue-700"
                          : "text-amber-700"
                      }
                    >
                      {doc.ocrConfidence}%
                    </span>
                  </td>
                  <td className="px-4 py-4 font-mono text-slate-800 font-semibold">
                    {doc.extractedFieldCount} Fields
                  </td>
                  <td className="px-4 py-4">
                    {doc.validationIssueCount > 0 ? (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-700 font-bold">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        {doc.validationIssueCount} Flagged
                      </span>
                    ) : (
                      <span className="text-emerald-700 font-semibold text-xs">0 Issues</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className="flex items-center justify-end space-x-2">
                      <button
                        onClick={() => setPreviewDoc(doc)}
                        className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                        title="Preview Document Details"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                      <Link href="/extraction">
                        <button
                          className="p-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-600 transition"
                          title="View Extracted Fields"
                        >
                          <FileCheck2 className="w-3.5 h-3.5" />
                        </button>
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Document Detail Preview Modal */}
      {previewDoc && (
        <Modal
          isOpen={true}
          onClose={() => setPreviewDoc(null)}
          title={`Document Inspector: ${previewDoc.fileName}`}
          subtitle={`Application ID: ${previewDoc.applicationId} • Type: ${previewDoc.documentType}`}
          maxWidth="2xl"
          footer={
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-slate-500 font-mono">
                SHA-256: {previewDoc.sha256Hash.slice(0, 24)}...
              </span>
              <Button variant="secondary" size="sm" onClick={() => setPreviewDoc(null)}>
                Close Preview
              </Button>
            </div>
          }
        >
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-600">File Classification:</span>
                <span className="font-bold text-slate-900">{previewDoc.documentType}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">File Size:</span>
                <span className="font-mono text-slate-800">{formatFileSize(previewDoc.fileSize)}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">OCR Mean Confidence:</span>
                <span className="font-mono text-emerald-700 font-bold">
                  {previewDoc.ocrConfidence}% (Amazon Textract / OCR Engine)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-600">Extracted Structured Fields:</span>
                <span className="font-mono text-indigo-700 font-bold">{previewDoc.extractedFieldCount} Points</span>
              </div>
            </div>

            <div className="p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
              <p className="font-bold text-indigo-900">Multi-Modal Extraction Summary</p>
              <p className="text-slate-700 mt-1 leading-relaxed">
                Optical character recognition and layout boundary analysis completed. Data points have been normalized into canonical Pydantic underwriting structures and queued for deterministic ratio validation.
              </p>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
