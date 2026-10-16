"use client";

import React, { useState } from "react";
import {
  Settings as SettingsIcon,
  User,
  Bell,
  Cpu,
  Database,
  Sliders,
  CheckCircle2,
  Save,
  Shield,
} from "lucide-react";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";

export default function SettingsPage() {
  const [savedNotice, setSavedNotice] = useState(false);

  // Preference states
  const [autoOcr, setAutoOcr] = useState(true);
  const [dtiCeiling, setDtiCeiling] = useState(45.0);
  const [ficoFloor, setFicoFloor] = useState(620);
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [criticalSmsAlerts, setCriticalSmsAlerts] = useState(false);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <PageHeader
        title="Underwriting System Settings & Preferences"
        subtitle="Configure underwriter workstation preferences, automated guideline thresholds, and API integration parameters."
        breadcrumbs={[
          { label: "Settings", href: "/settings" },
        ]}
        demoTag="PREFERENCES"
      />

      {savedNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-lg text-xs text-emerald-900 font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Workstation settings saved successfully.</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-6">
        {/* Profile Card */}
        <Card title="Underwriter Profile" subtitle="Active certified user session details.">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block text-slate-600 font-bold uppercase tracking-wider mb-1.5">Full Name</label>
              <input
                type="text"
                defaultValue="Catherine Hayes"
                disabled
                className="w-full bg-slate-100 border border-slate-300 rounded-lg px-3.5 py-2.5 text-slate-800 font-semibold cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-bold uppercase tracking-wider mb-1.5">Underwriter Identifier (NMLS / ID)</label>
              <input
                type="text"
                defaultValue="UW-4029 (Sr. Delegated Authority)"
                disabled
                className="w-full bg-slate-100 border border-slate-300 rounded-lg px-3.5 py-2.5 text-indigo-700 font-mono font-bold cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-bold uppercase tracking-wider mb-1.5">Assigned Branch / Division</label>
              <input
                type="text"
                defaultValue="National Prime Operations — Direct Lending"
                disabled
                className="w-full bg-slate-100 border border-slate-300 rounded-lg px-3.5 py-2.5 text-slate-800 cursor-not-allowed font-medium"
              />
            </div>
            <div>
              <label className="block text-slate-600 font-bold uppercase tracking-wider mb-1.5">Lending Authority Cap</label>
              <input
                type="text"
                defaultValue="$2,500,000.00 (Unconditional)"
                disabled
                className="w-full bg-slate-100 border border-slate-300 rounded-lg px-3.5 py-2.5 text-emerald-700 font-mono font-bold cursor-not-allowed"
              />
            </div>
          </div>
        </Card>

        {/* Automated Engine Preferences */}
        <Card title="Automated Guideline & Threshold Triggers" subtitle="Define local warning triggers for deterministic calculation workflows.">
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <div>
                <p className="font-bold text-slate-900">Auto-Trigger Multi-Modal OCR on Ingestion</p>
                <p className="text-xs text-slate-600 mt-0.5">
                  Automatically start layout recognition and entity extraction as soon as files are uploaded.
                </p>
              </div>
              <input
                type="checkbox"
                checked={autoOcr}
                onChange={(e) => setAutoOcr(e.target.checked)}
                className="w-5 h-5 rounded text-indigo-600 bg-white border-slate-300 focus:ring-indigo-500"
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <label className="block text-slate-700 font-bold mb-1.5">
                  Back-End DTI Warning Threshold (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={dtiCeiling}
                  onChange={(e) => setDtiCeiling(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-bold focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">Default agency ceiling is 45.0%</span>
              </div>

              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <label className="block text-slate-700 font-bold mb-1.5">
                  Qualifying FICO Minimum Floor
                </label>
                <input
                  type="number"
                  value={ficoFloor}
                  onChange={(e) => setFicoFloor(Number(e.target.value))}
                  className="w-full bg-white border border-slate-300 rounded-lg px-3 py-2 text-xs text-slate-900 font-mono font-bold focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <span className="text-[11px] text-slate-500 mt-1 block">Standard conforming minimum is 620</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Notifications */}
        <Card title="Alerts & Notification Routing" subtitle="Configure event subscriptions for underwriting queue items.">
          <div className="space-y-3 text-xs">
            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <div>
                <p className="font-bold text-slate-900">Email Notification on Critical Compliance Flags</p>
                <p className="text-xs text-slate-600 mt-0.5">
                  Receive instant alerts when a loan file triggers RESPA/TILA statutory alerts.
                </p>
              </div>
              <input
                type="checkbox"
                checked={emailAlerts}
                onChange={(e) => setEmailAlerts(e.target.checked)}
                className="w-5 h-5 rounded text-indigo-600 bg-white border-slate-300 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-xl bg-slate-50 border border-slate-200">
              <div>
                <p className="font-bold text-slate-900">High Risk AI Adverse Recommendation SMS</p>
                <p className="text-xs text-slate-600 mt-0.5">
                  Dispatch priority notice when MortgageGuard flags composite risk score &gt; 65.
                </p>
              </div>
              <input
                type="checkbox"
                checked={criticalSmsAlerts}
                onChange={(e) => setCriticalSmsAlerts(e.target.checked)}
                className="w-5 h-5 rounded text-indigo-600 bg-white border-slate-300 focus:ring-indigo-500"
              />
            </div>
          </div>
        </Card>

        {/* System Information */}
        <Card title="System Environment & Topology" subtitle="Connected back-end services, drivers, and API endpoints.">
          <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 font-mono text-xs space-y-2.5 text-slate-700">
            <div className="flex justify-between">
              <span className="text-slate-500 font-semibold">API Endpoint:</span>
              <span className="text-indigo-700 font-bold">http://localhost:8000/api/v1</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-semibold">Database Driver:</span>
              <span className="text-slate-900 font-medium">PostgreSQL (Asyncpg + SQLAlchemy)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-semibold">Model Orchestration:</span>
              <span className="text-slate-900 font-medium">LangGraph Multi-Agent Runtime</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-semibold">Application Version:</span>
              <span className="text-emerald-700 font-bold">v0.1.0 (Phase 0 Foundation)</span>
            </div>
          </div>
        </Card>

        {/* Save Button */}
        <div className="flex justify-end pt-2">
          <Button type="submit" variant="primary" size="md" leftIcon={<Save className="w-4 h-4" />}>
            Save Workstation Preferences
          </Button>
        </div>
      </form>
    </div>
  );
}
