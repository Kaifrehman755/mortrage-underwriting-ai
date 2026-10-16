import React from "react";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string | React.ReactNode;
  subtitle?: string | React.ReactNode;
  action?: React.ReactNode;
  footer?: React.ReactNode;
  demoLabel?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = "",
  title,
  subtitle,
  action,
  footer,
  demoLabel = false,
}) => {
  return (
    <div
      className={`bg-white border border-slate-200 rounded-xl shadow-sm transition hover:shadow-md hover:border-slate-300 flex flex-col ${className}`}
    >
      {(title || subtitle || action) && (
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between gap-4">
          <div>
            {typeof title === "string" ? (
              <div className="flex items-center gap-2">
                <h3 className="text-base font-bold text-slate-950 tracking-tight">{title}</h3>
              </div>
            ) : (
              title
            )}
            {subtitle && (
              <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">{subtitle}</p>
            )}
          </div>
          {action && <div className="flex items-center gap-2 shrink-0">{action}</div>}
        </div>
      )}
      <div className="p-6 flex-1 text-slate-700">{children}</div>
      {footer && (
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-100 rounded-b-xl text-xs text-slate-500">
          {footer}
        </div>
      )}
    </div>
  );
};
