"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Wand2, Loader2, Download, CheckCircle2, AlertCircle } from "lucide-react";
import Navbar from "@/components/Navbar";
import ResumePreview from "@/components/ResumePreview";
import { useAuthStore } from "@/lib/store";
import {
  getMasterResumes,
  getJobs,
  tailorResume,
  getTailoredResume,
  downloadPdf,
} from "@/lib/api";

interface Resume {
  id: string;
  filename?: string;
}
interface Job {
  id: string;
  title?: string;
  company?: string;
}

type Status = "idle" | "processing" | "completed" | "error";

export default function TailorPage() {
  const router = useRouter();
  const { isLoading, hydrate, isAuthenticated } = useAuthStore();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedResume, setSelectedResume] = useState("");
  const [selectedJob, setSelectedJob] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [tailoredId, setTailoredId] = useState("");
  const [previewSections, setPreviewSections] = useState<
    { title: string; items: { text: string; confidence?: number; modified?: boolean }[] }[]
  >([]);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated()) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated()) return;
    getMasterResumes().then(setResumes).catch(() => {});
    getJobs().then(setJobs).catch(() => {});
  }, [isAuthenticated]);

  const pollResult = useCallback(async (id: string) => {
    const maxAttempts = 30;
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const result = await getTailoredResume(id);
        if (result.status === "completed" || result.sections) {
          setStatus("completed");
          setPreviewSections(
            result.sections || [
              {
                title: "Summary",
                items: [
                  {
                    text: result.summary || "Resume tailored successfully.",
                    confidence: 0.95,
                    modified: true,
                  },
                ],
              },
            ]
          );
          return;
        }
        if (result.status === "error") {
          setStatus("error");
          setError(result.error || "Tailoring failed.");
          return;
        }
      } catch {
        // continue polling
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    setStatus("error");
    setError("Tailoring timed out. Please try again.");
  }, []);

  const handleTailor = async () => {
    if (!selectedResume || !selectedJob) return;
    setStatus("processing");
    setError("");
    setPreviewSections([]);
    try {
      const result = await tailorResume({
        master_resume_id: selectedResume,
        job_id: selectedJob,
      });
      setTailoredId(result.id);

      if (result.status === "completed" || result.sections) {
        setStatus("completed");
        setPreviewSections(
          result.sections || [
            {
              title: "Summary",
              items: [
                {
                  text: "Resume tailored successfully.",
                  confidence: 0.95,
                  modified: true,
                },
              ],
            },
          ]
        );
      } else {
        await pollResult(result.id);
      }
    } catch (err: unknown) {
      setStatus("error");
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Failed to start tailoring. Please try again.";
      setError(message);
    }
  };

  const handleDownload = async () => {
    if (!tailoredId) return;
    try {
      const blob = await downloadPdf(tailoredId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "tailored-resume.pdf";
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to download PDF.");
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-brand-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">
          Tailor Your Resume
        </h1>
        <p className="mb-8 text-sm text-gray-500">
          Select a master resume and a job description, then let our AI agents
          optimize your resume.
        </p>

        {/* Selection */}
        <div className="card mb-8">
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Master Resume
              </label>
              <select
                className="input-field"
                value={selectedResume}
                onChange={(e) => setSelectedResume(e.target.value)}
              >
                <option value="">Select a resume...</option>
                {resumes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.filename || `Resume ${r.id.slice(0, 8)}`}
                  </option>
                ))}
              </select>
              {resumes.length === 0 && (
                <p className="mt-1 text-xs text-gray-400">
                  No resumes uploaded yet.
                </p>
              )}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Job Description
              </label>
              <select
                className="input-field"
                value={selectedJob}
                onChange={(e) => setSelectedJob(e.target.value)}
              >
                <option value="">Select a job...</option>
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title ? `${j.title} — ${j.company}` : `Job ${j.id.slice(0, 8)}`}
                  </option>
                ))}
              </select>
              {jobs.length === 0 && (
                <p className="mt-1 text-xs text-gray-400">
                  No jobs added yet.
                </p>
              )}
            </div>
          </div>

          <button
            onClick={handleTailor}
            disabled={!selectedResume || !selectedJob || status === "processing"}
            className="btn-primary mt-6 w-full gap-2"
          >
            {status === "processing" ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Wand2 size={16} />
            )}
            {status === "processing" ? "AI Agents Working..." : "Tailor Resume"}
          </button>
        </div>

        {/* Status */}
        {status === "processing" && (
          <div className="card mb-8 border-brand-200 bg-brand-50">
            <div className="flex items-center gap-3">
              <Loader2 size={20} className="animate-spin text-brand-600" />
              <div>
                <p className="font-medium text-brand-900">
                  AI Pipeline Running
                </p>
                <p className="text-sm text-brand-700">
                  JD Normalizer → Company Enrichment → Resume Writer → QA
                  Auditor
                </p>
              </div>
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-brand-200">
              <div className="h-full animate-pulse rounded-full bg-brand-600 transition-all" style={{ width: "60%" }} />
            </div>
          </div>
        )}

        {status === "completed" && (
          <div className="mb-6 flex items-center justify-between rounded-xl border border-green-200 bg-green-50 px-4 py-3">
            <div className="flex items-center gap-2">
              <CheckCircle2 size={18} className="text-green-600" />
              <span className="text-sm font-medium text-green-800">
                Resume tailored successfully!
              </span>
            </div>
            <button onClick={handleDownload} className="btn-primary !py-2 !px-4 gap-2 text-xs">
              <Download size={14} />
              Download PDF
            </button>
          </div>
        )}

        {status === "error" && (
          <div className="mb-6 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-3">
            <AlertCircle size={18} className="text-red-600" />
            <span className="text-sm text-red-700">{error}</span>
          </div>
        )}

        {/* Preview */}
        {previewSections.length > 0 && (
          <ResumePreview sections={previewSections} />
        )}
      </main>
    </div>
  );
}
