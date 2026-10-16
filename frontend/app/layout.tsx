import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";

import { NavigationProvider } from "@/components/layout/NavigationContext";

export const metadata: Metadata = {
  title: "Mortgage Underwriting & Risk Assessment System",
  description: "Enterprise Financial Operations & Mortgage Underwriting Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 h-screen overflow-hidden antialiased flex font-sans selection:bg-slate-200 selection:text-slate-900">
        <NavigationProvider>
          <Sidebar />
          <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
            <Header />
            <main className="flex-1 p-4 sm:p-6 overflow-y-auto bg-slate-50/70">
              {children}
            </main>
          </div>
        </NavigationProvider>
      </body>
    </html>
  );
}
