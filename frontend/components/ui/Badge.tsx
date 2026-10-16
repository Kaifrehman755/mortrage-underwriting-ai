import React from "react";
import { ApplicationStatus, RiskLevel, ValidationSeverity } from "@/types";
import {
  getStatusBadgeClasses,
  getRiskBadgeClasses,
  getSeverityBadgeClasses,
} from "@/lib/formatters";

interface BadgeProps {
  children: React.ReactNode;
  variant?: "default" | "status" | "risk" | "severity" | "outline" | "demo";
  status?: ApplicationStatus;
  risk?: RiskLevel;
  severity?: ValidationSeverity;
  className?: string;
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = "default",
  status,
  risk,
  severity,
  className = "",
  size = "sm",
}) => {
  const sizeClasses = size === "sm" ? "text-xs px-2.5 py-0.5" : "text-sm px-3 py-1";

  let variantClasses = "bg-slate-800 text-slate-300 border-slate-700";

  if (variant === "status" && status) {
    variantClasses = getStatusBadgeClasses(status);
  } else if (variant === "risk" && risk) {
    variantClasses = getRiskBadgeClasses(risk);
  } else if (variant === "severity" && severity) {
    variantClasses = getSeverityBadgeClasses(severity);
  } else if (variant === "demo") {
    variantClasses = "bg-amber-500/10 text-amber-400 border-amber-500/30 font-mono tracking-wider font-semibold";
  } else if (variant === "outline") {
    variantClasses = "bg-transparent text-slate-300 border-slate-700";
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 font-medium rounded-full border ${sizeClasses} ${variantClasses} ${className}`}
    >
      {children}
    </span>
  );
};
