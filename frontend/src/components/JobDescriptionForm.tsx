"use client";

import { useState } from "react";
import { ClipboardPaste, Link2, Upload } from "lucide-react";
import clsx from "clsx";
import FileUpload from "./FileUpload";

type Tab = "paste" | "url" | "upload";

interface JobDescriptionFormProps {
  onSubmit: (data: {
    title: string;
    company: string;
    description?: string;
    url?: string;
    file?: File;
  }) => void;
  isLoading?: boolean;
}

export default function JobDescriptionForm({
  onSubmit,
  isLoading,
}: JobDescriptionFormProps) {
  const [tab, setTab] = useState<Tab>("paste");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [description, setDescription] = useState("");
  const [url, setUrl] = useState("");
  const [file, setFile] = useState<File | null>(null);

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: "paste", label: "Paste Text", icon: ClipboardPaste },
    { key: "url", label: "Enter URL", icon: Link2 },
    { key: "upload", label: "Upload File", icon: Upload },
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: Parameters<typeof onSubmit>[0] = { title, company };
    if (tab === "paste") data.description = description;
    else if (tab === "url") data.url = url;
    else if (tab === "upload" && file) data.file = file;
    onSubmit(data);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Title/Company */}
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Job Title
          </label>
          <input
            className="input-field"
            placeholder="e.g. Senior Software Engineer"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Company
          </label>
          <input
            className="input-field"
            placeholder="e.g. Google"
            value={company}
            onChange={(e) => setCompany(e.target.value)}
            required
          />
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-200 bg-gray-100 p-1">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            type="button"
            onClick={() => setTab(key)}
            className={clsx(
              "flex flex-1 items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition",
              tab === key
                ? "bg-white text-brand-700 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === "paste" && (
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Job Description
          </label>
          <textarea
            className="input-field min-h-[200px] resize-y"
            placeholder="Paste the full job description here..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
          />
        </div>
      )}

      {tab === "url" && (
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Job Posting URL
          </label>
          <input
            type="url"
            className="input-field"
            placeholder="https://careers.example.com/job/12345"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            required
          />
        </div>
      )}

      {tab === "upload" && (
        <FileUpload onFileSelect={(f) => setFile(f)} accept=".pdf,.docx,.txt" />
      )}

      <button type="submit" className="btn-primary w-full" disabled={isLoading}>
        {isLoading ? "Adding Job..." : "Add Job Description"}
      </button>
    </form>
  );
}
