"use client";

import React, { useState } from "react";
import Link from "next/link";
import { FileText, FileCode, UploadCloud } from "lucide-react";
import { UnderwritingDocument } from "@/types";
import { formatFileSize } from "@/lib/formatters";
import { Modal } from "@/components/ui/Modal";

interface SubmittedDocumentsRowProps {
  documents?: UnderwritingDocument[];
  compact?: boolean;
}

export const SubmittedDocumentsRow: React.FC<SubmittedDocumentsRowProps> = ({
  documents = [],
  compact = false,
}) => {
  const [selectedDoc, setSelectedDoc] = useState<UnderwritingDocument | null>(null);

  // If there are no documents, render clean empty state - NO mock data
  if (!documents || documents.length === 0) {
    if (compact) {
      return (
        <div className="flex items-center justify-between text-xs py-1 text-slate-400 font-mono">
          <span>No documents attached to this loan file</span>
          <Link href="/documents" className="text-slate-700 hover:text-slate-950 underline font-sans font-semibold">
            Upload Documents →
          </Link>
        </div>
      );
    }

    return (
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-3">
        <div className="flex items-center justify-between pb-3 border-b border-slate-100">
          <div>
            <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
              Submitted Documents
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Source files attached to the current loan file.
            </p>
          </div>
          <Link
            href="/documents"
            className="text-xs font-semibold text-slate-800 hover:text-slate-950 underline transition"
          >
            Manage Documents →
          </Link>
        </div>

        <div className="p-8 border border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-center space-y-2 bg-slate-50/50">
          <UploadCloud className="w-8 h-8 text-slate-400" />
          <p className="text-xs font-bold text-slate-700">No documents in current loan file</p>
          <p className="text-[11px] text-slate-400 max-w-sm">
            Documents uploaded through the intake pipeline or API will appear here for verification.
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {compact ? (
        <div className="flex flex-wrap items-center justify-end gap-2 text-xs">
          {documents.slice(0, 6).map((doc) => (
            <div
              key={doc.id}
              className="bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 flex items-center gap-2 shadow-2xs hover:border-slate-300 transition text-[11px]"
            >
              <FileText className="w-3.5 h-3.5 text-slate-500 shrink-0" />
              <span className="font-mono text-slate-800 font-semibold truncate max-w-[140px]" title={doc.fileName}>
                {doc.fileName}
              </span>
              <span className="text-[9px] uppercase font-mono text-slate-400 font-medium">
                {doc.documentType} • {formatFileSize(doc.fileSize || 0)}
              </span>
              <button
                type="button"
                onClick={() => setSelectedDoc(doc)}
                className="text-slate-800 hover:text-slate-950 font-bold text-[10px] ml-1 flex items-center gap-0.5"
              >
                Inspect
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-3 border-b border-slate-100 gap-2">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
                Submitted Documents
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Stored source files — open to verify or inspect OCR normalized data.
              </p>
            </div>
            <Link
              href="/documents"
              className="text-xs font-semibold text-slate-800 hover:text-slate-950 underline transition"
            >
              Manage all documents ({documents.length}) →
            </Link>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="p-3 bg-slate-50/60 border border-slate-200 rounded-xl flex items-center justify-between hover:bg-slate-50 hover:border-slate-300 transition"
              >
                <div className="flex items-center space-x-2.5 min-w-0">
                  <div className="w-8 h-8 rounded-lg bg-white border border-slate-200 flex items-center justify-center text-slate-700 shrink-0 shadow-2xs">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="truncate">
                    <p className="text-xs font-mono font-bold text-slate-900 truncate" title={doc.fileName}>
                      {doc.fileName}
                    </p>
                    <p className="text-[10px] text-slate-500 font-mono uppercase mt-0.5">
                      {doc.documentType} • {formatFileSize(doc.fileSize || 0)}
                    </p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedDoc(doc)}
                  className="px-2.5 py-1 text-xs font-semibold text-slate-700 hover:text-slate-950 bg-white hover:bg-slate-100 border border-slate-200 rounded-lg shadow-2xs transition shrink-0 ml-2"
                >
                  Inspect
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Document Review Modal */}
      {selectedDoc && (
        <Modal
          isOpen={!!selectedDoc}
          onClose={() => setSelectedDoc(null)}
          title={`Document: ${selectedDoc.fileName}`}
          maxWidth="lg"
        >
          <div className="space-y-4">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex items-center justify-between text-xs font-mono">
              <div>
                <span className="text-slate-500">Document Type: </span>
                <strong className="text-slate-900">{selectedDoc.documentType}</strong>
              </div>
              <div>
                <span className="text-slate-500">Size: </span>
                <strong className="text-slate-900">{formatFileSize(selectedDoc.fileSize || 0)}</strong>
              </div>
              <div>
                <span className="text-slate-500">Processing Status: </span>
                <strong className="text-slate-900 font-bold">{selectedDoc.processingStatus || "Validated"}</strong>
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl p-8 bg-slate-100 flex flex-col items-center justify-center text-center space-y-3">
              <FileCode className="w-12 h-12 text-slate-400" />
              <div>
                <p className="text-sm font-bold text-slate-800">{selectedDoc.fileName}</p>
                <p className="text-xs text-slate-500 mt-1">
                  Vault path: {selectedDoc.fileUrl || "/vault/documents/" + selectedDoc.fileName}
                </p>
              </div>
              <span className="text-xs px-3 py-1 rounded-full bg-slate-200 text-slate-800 font-bold border border-slate-300">
                {selectedDoc.ocrConfidence || 0}% OCR Confidence
              </span>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <Link
                href="/extraction"
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition"
              >
                Inspect Extracted Fields
              </Link>
            </div>
          </div>
        </Modal>
      )}
    </>
  );
};
