import Link from "next/link";
import { FileText, Sparkles, Shield, Zap } from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Nav */}
      <header className="border-b border-gray-200 bg-white/80 backdrop-blur-lg">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
              <FileText size={18} />
            </div>
            <span className="text-lg font-bold text-gray-900">
              Resume<span className="text-brand-600">Helper</span>
            </span>
          </Link>
          <div className="flex items-center gap-3">
            <Link href="/login" className="btn-secondary">
              Login
            </Link>
            <Link href="/register" className="btn-primary">
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-brand-50 via-white to-white">
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(45%_40%_at_50%_60%,rgba(99,102,241,0.08),transparent)]" />
        <div className="mx-auto max-w-4xl px-4 pb-24 pt-20 text-center sm:px-6 lg:px-8">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-1.5 text-sm font-medium text-brand-700">
            <Sparkles size={14} />
            Multi-Agent AI Orchestration
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 sm:text-5xl lg:text-6xl">
            Build ATS-Optimized
            <br />
            <span className="text-brand-600">Resumes with AI</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-gray-600">
            Our multi-agent pipeline analyzes job descriptions, enriches company
            data, and tailors your resume for maximum impact — all while
            preserving factual integrity with built-in anti-hallucination
            safeguards.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/register" className="btn-primary !px-8 !py-3 text-base">
              Get Started Free
            </Link>
            <Link href="/login" className="btn-secondary !px-8 !py-3 text-base">
              Login
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-gray-100 bg-white py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <h2 className="mb-12 text-center text-3xl font-bold text-gray-900">
            How It Works
          </h2>
          <div className="grid gap-8 md:grid-cols-3">
            {[
              {
                icon: FileText,
                title: "Upload Your Resume",
                desc: "Upload your master resume in PDF or DOCX format. We securely parse and store it.",
              },
              {
                icon: Zap,
                title: "Add a Job Description",
                desc: "Paste text, enter a URL, or upload a job posting. Our JD Normalizer extracts structured requirements.",
              },
              {
                icon: Shield,
                title: "AI Tailors Your Resume",
                desc: "Multiple AI agents collaborate to tailor, verify, and optimize your resume for ATS systems.",
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="card text-center">
                <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-100 text-brand-600">
                  <Icon size={24} />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900">
                  {title}
                </h3>
                <p className="text-sm leading-relaxed text-gray-600">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 bg-gray-50 py-8">
        <p className="text-center text-sm text-gray-500">
          &copy; {new Date().getFullYear()} ResumeHelper. Built with multi-agent AI.
        </p>
      </footer>
    </div>
  );
}
