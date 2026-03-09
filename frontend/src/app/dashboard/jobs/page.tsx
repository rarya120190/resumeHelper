"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, Plus, Trash2, Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import JobDescriptionForm from "@/components/JobDescriptionForm";
import { useAuthStore } from "@/lib/store";
import { getJobs, createJob } from "@/lib/api";

interface Job {
  id: string;
  title?: string;
  company?: string;
  created_at?: string;
  status?: string;
}

export default function JobsPage() {
  const router = useRouter();
  const { isLoading, hydrate, isAuthenticated } = useAuthStore();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [fetchLoading, setFetchLoading] = useState(true);

  useEffect(() => {
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (!isLoading && !isAuthenticated()) router.push("/login");
  }, [isLoading, isAuthenticated, router]);

  useEffect(() => {
    if (!isAuthenticated()) return;
    setFetchLoading(true);
    getJobs()
      .then(setJobs)
      .catch(() => {})
      .finally(() => setFetchLoading(false));
  }, [isAuthenticated]);

  const handleSubmit = async (data: {
    title: string;
    company: string;
    description?: string;
    url?: string;
    file?: File;
  }) => {
    setSubmitting(true);
    try {
      const newJob = await createJob(data);
      setJobs((prev) => [newJob, ...prev]);
      setShowForm(false);
    } catch {
      // handle silently
    } finally {
      setSubmitting(false);
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
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Job Descriptions
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Add and manage job descriptions to tailor resumes against.
            </p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="btn-primary gap-2"
          >
            <Plus size={16} />
            Add Job
          </button>
        </div>

        {/* Add Job Form */}
        {showForm && (
          <div className="card mb-8">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              New Job Description
            </h2>
            <JobDescriptionForm onSubmit={handleSubmit} isLoading={submitting} />
          </div>
        )}

        {/* Job List */}
        {fetchLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand-600" />
          </div>
        ) : jobs.length === 0 ? (
          <div className="card py-16 text-center">
            <Briefcase size={40} className="mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">No job descriptions added yet.</p>
            <p className="mt-1 text-sm text-gray-400">
              Click &quot;Add Job&quot; to add your first job description.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {jobs.map((j) => (
              <div
                key={j.id}
                className="card flex items-center justify-between !py-4"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-green-100 text-green-600">
                    <Briefcase size={20} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {j.title || "Untitled Job"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {j.company}
                      {j.created_at && (
                        <span className="ml-2 text-gray-400">
                          · {new Date(j.created_at).toLocaleDateString()}
                        </span>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {j.status && (
                    <span className="rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                      {j.status}
                    </span>
                  )}
                  <button className="rounded-lg p-2 text-gray-400 hover:bg-red-50 hover:text-red-500">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
