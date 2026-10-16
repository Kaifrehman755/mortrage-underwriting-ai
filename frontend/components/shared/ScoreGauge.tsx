import React from "react";

interface ScoreGaugeProps {
  score: number;
  maxScore?: number;
  minScore?: number;
  label: string;
  subLabel?: string;
  type?: "risk" | "credit" | "dti" | "ltv" | "generic";
  inverted?: boolean;
}

export const ScoreGauge: React.FC<ScoreGaugeProps> = ({
  score,
  maxScore = 100,
  minScore = 0,
  label,
  subLabel,
  type = "generic",
  inverted = false,
}) => {
  const percentage = Math.min(
    100,
    Math.max(0, ((score - minScore) / (maxScore - minScore)) * 100)
  );

  let colorClass = "text-indigo-600 stroke-indigo-600";

  if (type === "risk") {
    if (score < 30) {
      colorClass = "text-emerald-600 stroke-emerald-600";
    } else if (score < 65) {
      colorClass = "text-amber-500 stroke-amber-500";
    } else {
      colorClass = "text-rose-600 stroke-rose-600";
    }
  } else if (type === "credit") {
    if (score >= 740) {
      colorClass = "text-emerald-600 stroke-emerald-600";
    } else if (score >= 680) {
      colorClass = "text-blue-600 stroke-blue-600";
    } else if (score >= 620) {
      colorClass = "text-amber-500 stroke-amber-500";
    } else {
      colorClass = "text-rose-600 stroke-rose-600";
    }
  } else if (type === "dti") {
    if (score <= 36) {
      colorClass = "text-emerald-600 stroke-emerald-600";
    } else if (score <= 45) {
      colorClass = "text-amber-500 stroke-amber-500";
    } else {
      colorClass = "text-rose-600 stroke-rose-600";
    }
  }

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-slate-50 border border-slate-200 rounded-xl text-center">
      <div className="relative w-32 h-32 flex items-center justify-center">
        {/* SVG Circular Ring */}
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r="40"
            className="text-slate-200 stroke-current"
            strokeWidth="8"
            fill="transparent"
          />
          <circle
            cx="50"
            cy="50"
            r="40"
            className={`${colorClass} transition-all duration-1000 ease-out`}
            strokeWidth="8"
            strokeDasharray={`${2 * Math.PI * 40}`}
            strokeDashoffset={`${2 * Math.PI * 40 * (1 - percentage / 100)}`}
            strokeLinecap="round"
            fill="transparent"
          />
        </svg>

        {/* Center Score */}
        <div className="absolute flex flex-col items-center justify-center">
          <span className="text-2xl font-extrabold tracking-tight text-slate-900 font-mono">
            {score}
            {type === "dti" || type === "ltv" ? "%" : ""}
          </span>
          <span className="text-[10px] uppercase font-mono text-slate-500 font-semibold">
            {minScore}-{maxScore}
          </span>
        </div>
      </div>

      <div className="mt-2">
        <p className="text-xs font-semibold text-slate-900">{label}</p>
        {subLabel && <p className="text-[11px] text-slate-500 mt-0.5">{subLabel}</p>}
      </div>
    </div>
  );
};
