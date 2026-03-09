"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Upload,
  Plus,
  FileText,
  Briefcase,
  Wand2,
  Clock,
  ArrowRight,
} from "lucide-react";
import Navbar from "@/components/Navbar";
import { useAuthStore } from "@/lib/store";
import { getMasterResumes, getJobs, getTailoredResumes } from "@/lib/api";

interface Resume {
  id: string;
  filename?: string;
  created_at?: string;
}
interface Job {
  id: string;
  title?: string;
  company?: string;
  created_at?: string;
}
interface TailoredResume {
  id: string;
  job_title?: string;
  company?: string;
  created_at?: string;
  status?: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, isLoading, hydrate, isAuthenticated } = useAuthStore();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [tailored, setTailored] = useState<TailoredResume[]>([]);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated()) {
      router.push("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated()) return;
    getMasterResumes().then(setResumes).catch(() => {});
    getJobs().then(setJobs).catch(() => {});
    getTailoredResumes().then(setTailored).catch(() => {});
  }, [isAuthenticated]);

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

      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Welcome */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back{user?.name ? `, ${user.name}` : ""}!
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Manage your resumes, job descriptions, and tailored applications.
          </p>
        </div>

        {/* Quick Actions */}
        <div className="mb-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              href: "/dashboard/resumes",
              icon: Upload,
              label: "Upload Resume",
              desc: "Add a master resume",
              color: "bg-blue-100 text-blue-600",
            },
            {
              href: "/dashboard/jobs",
              icon: Plus,
              label: "Add Job",
              desc: "New job description",
              color: "bg-green-100 text-green-600",
            },
            {
              href: "/dashboard/tailor",
              icon: Wand2,
              label: "Tailor Resume",
              desc: "AI-powered tailoring",
              color: "bg-purple-100 text-purple-600",
            },
            {
              href: "/dashboard/resumes",
              icon: FileText,
              label: "My Resumes",
              desc: `${resumes.length} master resume${resumes.length !== 1 ? "s" : ""}`,
              color: "bg-amber-100 text-amber-600",
            },
          ].map(({ href, icon: Icon, label, desc, color }) => (
            <Link key={label} href={href} className="card group flex items-center gap-4 transition hover:shadow-md">
              <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${color}`}>
                <Icon size={22} />
              </div>
              <div>
                <p className="font-semibold text-gray-900 group-hover:text-brand-600">
                  {label}
                </p>
                <p className="text-xs text-gray-500">{desc}</p>
              </div>
            </Link>
          ))}
        </div>

        {/* Stats */}
        <div className="mb-10 grid gap-6 lg:grid-cols-2">
          {/* Master Resumes */}
          <div className="card">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
                <FileText size={18} className="text-brand-600" />
                Master Resumes
              </h2>
              <Link
                href="/dashboard/resumes"
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                View all
              </Link>
            </div>
            {resumes.length === 0 ? (
              <p className="py-6 text-center text-sm text-gray-400">
                No resumes uploaded yet.{" "}
                <Link href="/dashboard/resumes" className="text-brand-600 underline">
                  Upload one
                </Link>
              </p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {resumes.slice(0, 3).map((r) => (
                  <li key={r.id} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      <FileText size={16} className="text-gray-400" />
                      <span className="text-sm font-medium text-gray-700">
                        {r.filename || "Resume"}
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">
                      {r.created_at
                        ? new Date(r.created_at).toLocaleDateString()
                        : ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Jobs */}
          <div className="card">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
                <Briefcase size={18} className="text-brand-600" />
                Job Descriptions
              </h2>
              <Link
                href="/dashboard/jobs"
                className="text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                View all
              </Link>
            </div>
            {jobs.length === 0 ? (
              <p className="py-6 text-center text-sm text-gray-400">
                No jobs added yet.{" "}
                <Link href="/dashboard/jobs" className="text-brand-600 underline">
                  Add one
                </Link>
              </p>
            ) : (
              <ul className="divide-y divide-gray-100">
                {jobs.slice(0, 3).map((j) => (
                  <li key={j.id} className="flex items-center justify-between py-3">
                    <div>
                      <p className="text-sm font-medium text-gray-700">
                        {j.title || "Untitled"}
                      </p>
                      <p className="text-xs text-gray-400">{j.company}</p>
                    </div>
                    <span className="text-xs text-gray-400">
                      {j.created_at
                        ? new Date(j.created_at).toLocaleDateString()
                        : ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Recent Tailored Resumes */}
        <div className="card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="flex items-center gap-2 text-lg font-semibold text-gray-900">
              <Clock size={18} className="text-brand-600" />
              Recent Tailored Resumes
            </h2>
            <Link
              href="/dashboard/tailor"
              className="flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700"
            >
              Tailor new <ArrowRight size={14} />
            </Link>
          </div>
          {tailored.length === 0 ? (
            <p className="py-8 text-center text-sm text-gray-400">
              No tailored resumes yet. Select a resume and job to get started!
            </p>
          ) : (
            <ul className="divide-y divide-gray-100">
              {tailored.slice(0, 5).map((t) => (
                <li key={t.id} className="flex items-center justify-between py-3">
                  <div>
                    <p className="text-sm font-medium text-gray-700">
                      {t.job_title || "Tailored Resume"}
                    </p>
                    <p className="text-xs text-gray-400">{t.company}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                      {t.status || "completed"}
                    </span>
                    <span className="text-xs text-gray-400">
                      {t.created_at
                        ? new Date(t.created_at).toLocaleDateString()
                        : ""}
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
    </div>
  );
}
