"use client";

import React from "react";
import { History, Clock, ArrowRight, ShieldCheck } from "lucide-react";
import { AuditEvent } from "@/types";
import { formatDate } from "@/lib/formatters";

interface CaseVersionHistoryProps {
  applicationId?: string;
  auditTrail?: AuditEvent[];
}

export const CaseVersionHistory: React.FC<CaseVersionHistoryProps> = ({
  applicationId,
  auditTrail = [],
}) => {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
      {/* Title & Subtitle */}
      <div className="pb-3 border-b border-slate-100 flex items-start justify-between">
        <div>
          <h3 className="text-base font-extrabold text-slate-900 tracking-tight">
            Case Revision History
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Audit trail of corrections and underwriting reruns for {applicationId || "selected file"}.
          </p>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 border border-slate-200 font-semibold">
          {auditTrail.length} Events Logged
        </span>
      </div>

      {/* Version History List / Clean Blank State */}
      {auditTrail.length === 0 ? (
        <div className="p-8 border border-dashed border-slate-200 rounded-xl flex flex-col items-center justify-center text-center space-y-2 bg-slate-50/50">
          <History className="w-8 h-8 text-slate-400" />
          <p className="text-xs font-bold text-slate-700">No revisions recorded</p>
          <p className="text-[11px] text-slate-400 max-w-sm">
            This loan file is at its baseline version. Any underwriter adjustments or data corrections will be recorded here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {auditTrail.slice(0, 5).map((evt, idx) => (
            <div
              key={evt.id || idx}
              className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50 hover:bg-slate-50 transition space-y-2.5"
            >
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between text-xs gap-1.5">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-slate-900 font-mono">
                    {evt.action || "Underwriting Event"}
                  </span>
                  <span className="text-slate-400">•</span>
                  <div className="flex items-center text-slate-500 font-mono text-[11px]">
                    <Clock className="w-3 h-3 mr-1" />
                    <span>{formatDate(evt.timestamp)}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 font-mono text-xs">
                  <span className="px-2 py-0.5 rounded bg-slate-200 text-slate-800 font-bold">
                    {evt.status || "LOGGED"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 pt-2 border-t border-slate-200/60 text-xs">
                <div>
                  <span className="text-[10px] uppercase font-mono text-slate-400 block font-semibold">
                    Actor
                  </span>
                  <span className="font-semibold text-slate-900">
                    {evt.actorName} ({evt.actorType})
                  </span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-mono text-slate-400 block font-semibold">
                    Details
                  </span>
                  <span className="text-slate-600">{evt.details}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
