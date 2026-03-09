"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { FileText, Plus, Trash2, Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import FileUpload from "@/components/FileUpload";
import { useAuthStore } from "@/lib/store";
import { getMasterResumes, createMasterResume } from "@/lib/api";

interface Resume {
  id: string;
  filename?: string;
  created_at?: string;
}

export default function ResumesPage() {
  const router = useRouter();
  const { isLoading, hydrate, isAuthenticated } = useAuthStore();
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [showUpload, setShowUpload] = useState(false);
  const [uploading, setUploading] = useState(false);
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
    getMasterResumes()
      .then(setResumes)
      .catch(() => {})
      .finally(() => setFetchLoading(false));
  }, [isAuthenticated]);

  const handleUpload = async (file: File) => {
    setUploading(true);
    try {
      const newResume = await createMasterResume(file);
      setResumes((prev) => [newResume, ...prev]);
      setShowUpload(false);
    } catch {
      // handle silently
    } finally {
      setUploading(false);
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
              Master Resumes
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              Upload and manage your master resumes.
            </p>
          </div>
          <button
            onClick={() => setShowUpload(!showUpload)}
            className="btn-primary gap-2"
          >
            <Plus size={16} />
            Upload New
          </button>
        </div>

        {/* Upload Section */}
        {showUpload && (
          <div className="card mb-8">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
              Upload Resume
            </h2>
            <FileUpload onFileSelect={handleUpload} />
            {uploading && (
              <div className="mt-4 flex items-center gap-2 text-sm text-brand-600">
                <Loader2 size={14} className="animate-spin" />
                Uploading...
              </div>
            )}
          </div>
        )}

        {/* Resume List */}
        {fetchLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 size={24} className="animate-spin text-brand-600" />
          </div>
        ) : resumes.length === 0 ? (
          <div className="card py-16 text-center">
            <FileText size={40} className="mx-auto mb-4 text-gray-300" />
            <p className="text-gray-500">No resumes uploaded yet.</p>
            <p className="mt-1 text-sm text-gray-400">
              Click &quot;Upload New&quot; to add your first master resume.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {resumes.map((r) => (
              <div
                key={r.id}
                className="card flex items-center justify-between !py-4"
              >
                <div className="flex items-center gap-4">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-brand-600">
                    <FileText size={20} />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">
                      {r.filename || "Resume"}
                    </p>
                    <p className="text-xs text-gray-400">
                      {r.created_at
                        ? `Uploaded ${new Date(r.created_at).toLocaleDateString()}`
                        : ""}
                    </p>
                  </div>
                </div>
                <button className="rounded-lg p-2 text-gray-400 hover:bg-red-50 hover:text-red-500">
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
