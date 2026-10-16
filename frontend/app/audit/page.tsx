"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  History,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Info,
  Filter,
  Search,
  Lock,
  ArrowRight,
  User,
  Cpu,
  Bot,
  Scale,
} from "lucide-react";
import { auditService } from "@/services/auditService";
import { AuditEvent } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { formatDateTime } from "@/lib/formatters";

export default function AuditTrailPage() {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("All");

  const loadAudit = async () => {
    setLoading(true);
    try {
      const data = await auditService.getAuditTrail();
      setEvents(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAudit();
  }, []);

  const filteredEvents = events.filter((ev) => {
    const matchesCat = categoryFilter === "All" || ev.category === categoryFilter;
    const matchesSearch =
      searchQuery.trim() === "" ||
      ev.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.actorName.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.applicationId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      ev.details.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Immutable Underwriting Audit Trail & System Ledger"
        subtitle="Chronological, tamper-evident audit logs capturing every automated OCR extraction, model inference, compliance check, and underwriter action."
        breadcrumbs={[
          { label: "Audit Trail", href: "/audit" },
        ]}
        demoTag="AUDIT LEDGER ACTIVE"
      />

      <DemoBanner
        moduleName="Immutable Audit Trail Engine"
        message="Simulating append-only event logging. In production, events are committed with cryptographic hash chains to ensure regulatory audit compliance."
      />

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white border border-slate-200 shadow-sm rounded-xl p-3.5 px-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search audit actions, actors, or application IDs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 rounded-lg pl-9 pr-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium"
          />
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-y-2">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-600 font-bold uppercase tracking-wider">Category:</span>
          {["All", "Creation", "Document", "Extraction", "Calculation", "Compliance", "Decision"].map(
            (cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition ${
                  categoryFilter === cat
                    ? "bg-indigo-600 text-white shadow-sm"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200 hover:text-slate-900"
                }`}
              >
                {cat}
              </button>
            )
          )}
        </div>
      </div>

      {/* Audit Timeline */}
      <Card title="Chronological Event Stream" subtitle="Append-only record of all actions in the mortgage lifecycle.">
        <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-3 before:bottom-3 before:w-[2px] before:bg-slate-200">
          {filteredEvents.map((event) => {
            let actorIcon = <User className="w-3.5 h-3.5 text-indigo-600" />;
            if (event.actorType === "System") actorIcon = <Cpu className="w-3.5 h-3.5 text-blue-600" />;
            if (event.actorType === "AI Agent") actorIcon = <Bot className="w-3.5 h-3.5 text-purple-600" />;
            if (event.actorType === "Compliance Engine") actorIcon = <Scale className="w-3.5 h-3.5 text-amber-600" />;

            return (
              <div key={event.id} className="relative group">
                {/* Timeline Dot */}
                <div className="absolute -left-6 top-1.5 w-5 h-5 rounded-full bg-white border-2 border-indigo-600 flex items-center justify-center text-indigo-600 shadow-sm group-hover:scale-110 transition">
                  <div className="w-2 h-2 rounded-full bg-indigo-600" />
                </div>

                {/* Event Card */}
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 hover:border-indigo-300 transition space-y-2">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-bold text-slate-900 text-xs">{event.action}</span>
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-200 text-slate-800 border border-slate-300">
                        {event.category}
                      </span>
                      <span className="text-[10px] font-mono font-bold text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                        {event.applicationId}
                      </span>
                    </div>

                    <span className="text-xs font-mono text-slate-500 font-medium">
                      {formatDateTime(event.timestamp)}
                    </span>
                  </div>

                  <p className="text-xs text-slate-700 leading-relaxed font-medium">{event.details}</p>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200 text-xs font-mono text-slate-500">
                    <span className="flex items-center gap-1.5">
                      {actorIcon}
                      Actor: <strong className="text-slate-800">{event.actorName}</strong> ({event.actorType})
                    </span>
                    <span className="flex items-center gap-1 text-emerald-700 font-bold">
                      <Lock className="w-3.5 h-3.5 text-emerald-600" />
                      SHA-256 Verified
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
