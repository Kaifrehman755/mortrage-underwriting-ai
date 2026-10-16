import React from "react";
import { AlertTriangle, Info } from "lucide-react";

interface DemoBannerProps {
  moduleName?: string;
  message?: string;
  className?: string;
}

export const DemoBanner: React.FC<DemoBannerProps> = () => {
  return null;
};

export const DisclaimerBox: React.FC<{ text: string; className?: string }> = ({
  text,
  className = "",
}) => {
  return (
    <div
      className={`bg-slate-100/90 border border-slate-200 rounded-lg p-3 flex items-center gap-2.5 text-xs text-slate-600 font-mono ${className}`}
    >
      <Info className="w-4 h-4 text-indigo-600 shrink-0" />
      <span className="leading-relaxed">{text}</span>
    </div>
  );
};
