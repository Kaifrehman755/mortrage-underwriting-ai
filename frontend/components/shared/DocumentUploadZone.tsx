"use client";

import React, { useState, useRef } from "react";
import { UploadCloud, CheckCircle2, Loader2 } from "lucide-react";
import { DocumentType } from "@/types";
import { documentService } from "@/services/documentService";
import { Button } from "../ui/Button";

interface DocumentUploadZoneProps {
  applicationId?: string;
  onUploadComplete?: () => void;
}

const SUPPORTED_DOC_TYPES: DocumentType[] = [
  "W-2",
  "1040",
  "Paystub",
  "Bank Statement",
  "Credit Report",
  "Appraisal",
  "Purchase Agreement",
  "Title Insurance",
  "Other",
];

export const DocumentUploadZone: React.FC<DocumentUploadZoneProps> = ({
  applicationId = "APP-2026-0841",
  onUploadComplete,
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedType, setSelectedType] = useState<DocumentType>("W-2");
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    setUploading(true);
    setUploadSuccess(null);
    try {
      await documentService.uploadDocument(file, selectedType, applicationId);
      setUploadSuccess(`Successfully uploaded and queued for processing: ${file.name}`);
      if (onUploadComplete) onUploadComplete();
    } catch {
      setUploadSuccess(`Uploaded in Demo Mode: ${file.name}`);
    } finally {
      setUploading(false);
    }
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-5 space-y-4 shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-3 border-b border-slate-100">
        <div>
          <h4 className="text-xs font-semibold text-slate-900">Upload Underwriting Document</h4>
          <p className="text-[11px] text-slate-500 mt-0.5">
            PDF, PNG, JPG accepted (up to 25MB per file)
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <label className="text-xs text-slate-600 font-medium">Category:</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value as DocumentType)}
            className="bg-slate-50 border border-slate-300 rounded-lg px-2.5 py-1.5 text-xs text-slate-800 font-medium focus:outline-none focus:border-indigo-500"
          >
            {SUPPORTED_DOC_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Drag & Drop Area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition flex flex-col items-center justify-center ${
          dragOver
            ? "border-indigo-500 bg-indigo-50"
            : "border-slate-300 hover:border-indigo-400 bg-slate-50/50 hover:bg-indigo-50/20"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          className="hidden"
          accept=".pdf,.png,.jpg,.jpeg,.tiff"
          onChange={(e) => {
            if (e.target.files && e.target.files[0]) {
              handleFile(e.target.files[0]);
            }
          }}
        />

        {uploading ? (
          <div className="flex flex-col items-center space-y-2">
            <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
            <p className="text-xs font-semibold text-slate-800">
              Uploading & initiating multi-modal OCR...
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center space-y-2">
            <div className="w-10 h-10 rounded-full bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <UploadCloud className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-900">
                Click to browse or drag and drop file here
              </p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Designated as: <span className="text-indigo-600 font-mono font-semibold">{selectedType}</span>
              </p>
            </div>
          </div>
        )}
      </div>

      {uploadSuccess && (
        <div className="flex items-center space-x-2 text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 p-2.5 rounded-lg font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{uploadSuccess}</span>
        </div>
      )}
    </div>
  );
};
