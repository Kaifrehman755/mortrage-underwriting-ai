"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building,
  MapPin,
  DollarSign,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Layers,
  ArrowRight,
  TrendingUp,
} from "lucide-react";
import { propertyService } from "@/services/propertyService";
import { PropertyDetails } from "@/types";
import { PageHeader } from "@/components/layout/PageHeader";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { DemoBanner } from "@/components/ui/DemoBanner";
import { formatCurrency, formatDate } from "@/lib/formatters";

export default function PropertyValuationPage() {
  const [property, setProperty] = useState<PropertyDetails | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    propertyService.getPropertyValuation().then((data) => {
      setProperty(data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        title="Collateral Risk & Property Valuation"
        subtitle="Appraisal dataset verification, market comparable analysis, and collateral equity adequacy assessment."
        breadcrumbs={[
          { label: "Financial Analysis", href: "/financial" },
          { label: "Property Valuation" },
        ]}
        demoTag="DEMO PROPERTY DATA"
        actions={
          <div className="flex items-center space-x-2">
            <Link href="/compliance">
              <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                Proceed to Compliance Engine
              </Button>
            </Link>
          </div>
        }
      />

      <DemoBanner
        moduleName="Property Valuation Engine"
        message="Displaying simulated Uniform Appraisal Dataset (UAD) findings and comparable sales adjustments pending full backend appraisal integration."
      />

      {/* Property Overview Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Reconciled Appraised Value</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-1 font-mono">
            {formatCurrency(property?.estimatedAppraisedValue || 815000)}
          </p>
          <div className="mt-2 text-xs text-emerald-700 font-semibold font-mono flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Confidence: {property?.valuationConfidence || 94}%
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Subject Property Type</span>
          <p className="text-xl font-bold text-slate-900 mt-1">
            {property?.propertyType.replace(/_/g, " ") || "Single Family"}
          </p>
          <div className="mt-2 text-xs text-slate-500 font-mono">
            Built in {property?.yearBuilt || 2019} • {property?.unitsCount || 1} Unit
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Gross Living Area (GLA)</span>
          <p className="text-3xl font-extrabold text-slate-900 mt-1 font-mono">
            {property?.squareFeet.toLocaleString() || "3,120"} <span className="text-sm font-medium text-slate-500">sq ft</span>
          </p>
          <div className="mt-2 text-xs text-slate-500 font-mono">
            {property?.bedrooms || 4} Beds • {property?.bathrooms || 3.5} Baths
          </div>
        </div>

        <div className="p-5 rounded-xl bg-white border border-slate-200 shadow-sm hover:border-slate-300 transition">
          <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Certified Appraiser</span>
          <p className="text-sm font-bold text-slate-900 mt-1 truncate">
            {property?.appraiserName || "Robert G. Chen, MAI"}
          </p>
          <div className="mt-2 text-xs text-slate-500 font-mono">
            Date: {formatDate(property?.appraisalDate || "2026-10-02")}
          </div>
        </div>
      </div>

      {/* Property Details Card */}
      <Card title="Subject Property Specification" subtitle="Verified property address and parcel boundaries.">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Street Address:</span>
            <p className="text-slate-900 font-bold mt-0.5">{property?.address.street}</p>
            <p className="text-slate-600 mt-0.5">
              {property?.address.city}, {property?.address.state} {property?.address.zipCode}
            </p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Occupancy Intent:</span>
            <p className="text-slate-900 font-bold mt-0.5">
              {property?.occupancyType.replace(/_/g, " ")}
            </p>
            <p className="text-slate-600 mt-0.5">County: {property?.address.county}</p>
          </div>

          <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200">
            <span className="text-slate-500 font-semibold uppercase tracking-wider text-[10px]">Parcel Number (APN):</span>
            <p className="text-indigo-700 font-mono font-bold mt-0.5">
              {property?.parcelNumber || "TRAV-2019-902-88"}
            </p>
            <p className="text-slate-600 mt-0.5">Lot Size: {property?.lotSizeAcres || 0.28} Acres</p>
          </div>
        </div>
      </Card>

      {/* Comparable Sales Analysis Table */}
      <Card
        title="Comparable Market Properties (Comps)"
        subtitle="Recent closed arm's length sales in proximity supporting the appraised subject valuation."
      >
        <div className="overflow-x-auto -mx-6">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-600 font-mono uppercase text-[10px] tracking-wider border-y border-slate-200">
              <tr>
                <th className="px-6 py-3.5">Comparable Property</th>
                <th className="px-4 py-3.5">Sale Price</th>
                <th className="px-4 py-3.5">Sale Date</th>
                <th className="px-4 py-3.5">Size (Sq Ft)</th>
                <th className="px-4 py-3.5">Price / Sq Ft</th>
                <th className="px-4 py-3.5">Distance</th>
                <th className="px-4 py-3.5">Net Adjustment</th>
                <th className="px-6 py-3.5 text-right">Adjusted Indicated Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
              {property?.comparables?.map((comp) => (
                <tr key={comp.id} className="hover:bg-slate-50 transition">
                  <td className="px-6 py-4">
                    <p className="font-bold text-slate-900">{comp.address}</p>
                    <p className="text-[11px] text-slate-500 font-mono">
                      {comp.bedrooms} Bed • {comp.bathrooms} Bath
                    </p>
                  </td>
                  <td className="px-4 py-4 font-mono font-bold text-slate-900">
                    {formatCurrency(comp.salePrice)}
                  </td>
                  <td className="px-4 py-4 font-mono text-slate-600">
                    {formatDate(comp.saleDate)}
                  </td>
                  <td className="px-4 py-4 font-mono text-slate-700">
                    {comp.squareFeet.toLocaleString()} sq ft
                  </td>
                  <td className="px-4 py-4 font-mono text-slate-700">
                    ${comp.pricePerSqFt.toFixed(2)}/sq ft
                  </td>
                  <td className="px-4 py-4 font-mono text-slate-700">
                    {comp.distanceMiles} miles
                  </td>
                  <td className="px-4 py-4 font-mono">
                    <span className={comp.netAdjustment < 0 ? "text-rose-600 font-bold" : "text-emerald-700 font-bold"}>
                      {comp.netAdjustment < 0 ? "-" : "+"}
                      {formatCurrency(Math.abs(comp.netAdjustment))}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right font-mono font-extrabold text-indigo-700">
                    {formatCurrency(comp.adjustedValue)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
