"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

export interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, className = "" }) => {
  return (
    <nav className={`flex items-center space-x-1 text-xs text-slate-500 font-medium ${className}`} aria-label="Breadcrumb">
      <Link
        href="/dashboard"
        className="flex items-center hover:text-slate-950 transition p-1 rounded hover:bg-slate-200/60 text-slate-500"
      >
        <Home className="w-3.5 h-3.5" />
      </Link>
      {items.map((item, idx) => {
        const isLast = idx === items.length - 1;
        return (
          <React.Fragment key={idx}>
            <ChevronRight className="w-3 h-3 text-slate-400 shrink-0" />
            {item.href && !isLast ? (
              <Link href={item.href} className="hover:text-slate-950 transition">
                {item.label}
              </Link>
            ) : (
              <span className="text-slate-900 font-semibold truncate max-w-xs">{item.label}</span>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};
