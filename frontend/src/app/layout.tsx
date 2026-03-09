import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Resume Helper — AI-Powered Resume Tailoring",
  description:
    "Build ATS-optimized resumes with multi-agent AI orchestration. Tailor your resume for every job application.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 font-sans">{children}</body>
    </html>
  );
}
