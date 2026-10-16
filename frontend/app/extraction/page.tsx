"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  AlertTriangle,
  Edit3,
  FileText,
  Filter,
  Save,
  ArrowRight,
} from "lucide-react";
import { documentService } from "@/services/documentService";
import { ExtractedField } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { DemoBanner } from "@/components/ui/DemoBanner";

export default function ExtractionReviewPage() {
  const [fields, setFields] = useState<ExtractedField[]>([]);
  const [loading, setLoading] = useState(true);
  const [editingField, setEditingField] = useState<ExtractedField | null>(null);
  const [editValue, setEditValue] = useState<string>("");
  const [editNote, setEditNote] = useState<string>("");
  const [categoryFilter, setCategoryFilter] = useState<string>("All");

  const loadFields = async () => {
    setLoading(true);
    try {
      const data = await documentService.getExtractedFields();
      setFields(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFields();
  }, []);

  const handleOpenEdit = (field: ExtractedField) => {
    setEditingField(field);
    setEditValue(String(field.normalizedValue));
    setEditNote(field.underwriterNote || "");
  };

  const handleSaveEdit = async () => {
    if (!editingField) return;
    try {
      await documentService.updateExtractedField(editingField.id, editValue, editNote);
      await loadFields();
      setEditingField(null);
    } catch {
      setFields((prev) =>
        prev.map((f) =>
          f.id === editingField.id
            ? {
                ...f,
                normalizedValue: editValue,
                validationStatus: "Edited",
                underwriterNote: editNote,
              }
            : f
        )
      );
      setEditingField(null);
    }
  };

  const filteredFields =
    categoryFilter === "All"
      ? fields
      : fields.filter((f) => f.category === categoryFilter);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="OCR Data Extraction & Verification Review"
        subtitle="Inspect, audit, and correct OCR-extracted key-value pairs with source document lineage and confidence metrics."
        breadcrumbs={[
          { label: "Document Center", href: "/documents" },
          { label: "Data Extraction" },
        ]}
        demoTag="DEMO DATA"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/validation">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to Validation Engine
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Data Extraction Review"
        message="Underwriters can inspect optical recognition confidence and override extracted values. All adjustments create immutable audit records."
      />

      {/* Filter Tabs */}
      <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-3 px-4 shadow-xs">
        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-slate-500" />
          <span className="text-xs text-slate-700 font-semibold">Category:</span>
          {["All", "Income", "Asset", "Property", "Tax"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                categoryFilter === cat
                  ? "bg-slate-900 text-white shadow-xs"
                  : "bg-slate-100 text-slate-600 hover:text-slate-900 hover:bg-slate-200"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <span className="text-xs text-slate-500 font-mono font-medium">
          {filteredFields.length} Extracted Points
        </span>
      </div>

      {/* Extracted Fields Table */}
      <Card className="p-0 overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] tracking-wider border-b border-slate-200 font-bold">
              <tr>
                <th className="px-6 py-3.5">Field Name</th>
                <th className="px-4 py-3.5">Category</th>
                <th className="px-4 py-3.5">Normalized Value</th>
                <th className="px-4 py-3.5">Raw OCR Value</th>
                <th className="px-4 py-3.5">Confidence</th>
                <th className="px-4 py-3.5">Source Document</th>
                <th className="px-4 py-3.5">Status</th>
                <th className="px-6 py-3.5 text-right">Edit</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {filteredFields.map((field) => (
                <tr key={field.id} className="hover:bg-indigo-50/40 transition">
                  <td className="px-6 py-4">
                    <p className="font-bold text-slate-900">{field.fieldName}</p>
                    {field.underwriterNote && (
                      <p className="text-[10px] text-amber-700 mt-0.5 font-mono font-semibold">
                        Note: {field.underwriterNote}
                      </p>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <span className="px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200 text-[10px] font-mono font-semibold">
                      {field.category}
                    </span>
                  </td>
                  <td className="px-4 py-4 font-mono font-bold text-slate-900">
                    {typeof field.normalizedValue === "number"
                      ? field.normalizedValue.toLocaleString("en-US", {
                          style: field.category === "Income" || field.category === "Asset" ? "currency" : "decimal",
                          currency: "USD",
                          maximumFractionDigits: 0,
                        })
                      : field.normalizedValue}
                  </td>
                  <td className="px-4 py-4 font-mono text-slate-500 text-[11px]">
                    {field.rawExtractedValue}
                  </td>
                  <td className="px-4 py-4 font-mono font-bold">
                    <span
                      className={
                        field.confidence >= 97
                          ? "text-emerald-700"
                          : field.confidence >= 90
                          ? "text-blue-700"
                          : "text-amber-700"
                      }
                    >
                      {field.confidence}%
                    </span>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-1.5 text-slate-700">
                      <FileText className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                      <span className="truncate max-w-[180px] font-mono text-[11px]">
                        {field.documentName} (p.{field.sourcePage})
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    {field.validationStatus === "Verified" ? (
                      <span className="inline-flex items-center gap-1 text-xs text-emerald-700 font-semibold">
                        <CheckCircle2 className="w-3.5 h-3.5" /> Verified
                      </span>
                    ) : field.validationStatus === "Edited" ? (
                      <span className="inline-flex items-center gap-1 text-xs text-indigo-700 font-bold font-mono">
                        <Edit3 className="w-3.5 h-3.5" /> Adjusted
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-xs text-amber-700 font-bold">
                        <AlertTriangle className="w-3.5 h-3.5" /> Flagged
                      </span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button
                      onClick={() => handleOpenEdit(field)}
                      className="p-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
                      title="Override Extracted Value"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Edit Extracted Field Modal */}
      {editingField && (
        <Modal
          isOpen={true}
          onClose={() => setEditingField(null)}
          title={`Override Field: ${editingField.fieldName}`}
          subtitle={`Source: ${editingField.documentName} (Page ${editingField.sourcePage}) • OCR Confidence: ${editingField.confidence}%`}
          maxWidth="md"
          footer={
            <div className="flex items-center justify-end space-x-2">
              <Button variant="outline" size="sm" onClick={() => setEditingField(null)}>
                Cancel
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleSaveEdit}
                leftIcon={<Save className="w-3.5 h-3.5" />}
              >
                Save Adjustment
              </Button>
            </div>
          }
        >
          <div className="space-y-4 text-xs">
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-slate-500 font-mono text-[10px] font-bold">RAW OCR DETECTED STRING:</span>
              <p className="text-slate-800 font-mono text-xs font-semibold">{editingField.rawExtractedValue}</p>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Underwriter Adjusted Normalized Value
              </label>
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full bg-slate-50 border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-semibold focus:outline-none focus:border-indigo-500 focus:bg-white"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">
                Underwriter Justification / Reason Note (Required)
              </label>
              <textarea
                rows={3}
                value={editNote}
                onChange={(e) => setEditNote(e.target.value)}
                placeholder="e.g. Sourced additional verification from YTD paystub line 4..."
                className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:bg-white"
              />
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
