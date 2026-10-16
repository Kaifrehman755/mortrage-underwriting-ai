import React from "react";
import { Loader2 } from "lucide-react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = "primary",
  size = "md",
  isLoading = false,
  leftIcon,
  rightIcon,
  className = "",
  disabled,
  ...props
}) => {
  const sizeClasses = {
    sm: "px-3 py-1.5 text-xs rounded-lg gap-1.5",
    md: "px-4 py-2 text-sm rounded-lg gap-2",
    lg: "px-5 py-2.5 text-base rounded-lg gap-2.5",
  }[size];

  const variantClasses = {
    primary:
      "bg-slate-900 hover:bg-slate-800 text-white font-medium shadow-sm hover:shadow active:bg-slate-950 disabled:bg-slate-300",
    secondary:
      "bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium border border-slate-200 active:bg-slate-300 disabled:bg-slate-50",
    outline:
      "bg-white hover:bg-slate-50 text-slate-700 font-medium border border-slate-300 hover:border-slate-400 active:bg-slate-100 shadow-sm",
    ghost:
      "bg-transparent hover:bg-slate-100 text-slate-600 hover:text-slate-900 font-medium",
    danger:
      "bg-rose-600 hover:bg-rose-700 text-white font-medium shadow-sm active:bg-rose-800 disabled:bg-rose-300",
    success:
      "bg-emerald-600 hover:bg-emerald-700 text-white font-medium shadow-sm active:bg-emerald-800 disabled:bg-emerald-300",
  }[variant];

  return (
    <button
      className={`inline-flex items-center justify-center transition focus:outline-none focus:ring-2 focus:ring-slate-500/40 focus:ring-offset-2 select-none disabled:opacity-50 disabled:cursor-not-allowed ${sizeClasses} ${variantClasses} ${className}`}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <Loader2 className="w-4 h-4 animate-spin text-current" />
      ) : (
        leftIcon && <span className="shrink-0">{leftIcon}</span>
      )}
      <span>{children}</span>
      {!isLoading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
    </button>
  );
};
