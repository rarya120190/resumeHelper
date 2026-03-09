"use client";

import { useCallback, useState } from "react";
import { Upload, FileUp, X } from "lucide-react";
import clsx from "clsx";

interface FileUploadProps {
  accept?: string;
  onFileSelect: (file: File) => void;
  className?: string;
}

export default function FileUpload({
  accept = ".pdf,.docx",
  onFileSelect,
  className,
}: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleFile = useCallback(
    (file: File) => {
      setSelectedFile(file);
      onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragActive(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const clearFile = () => {
    setSelectedFile(null);
  };

  return (
    <div className={className}>
      {!selectedFile ? (
        <label
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={clsx(
            "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition",
            dragActive
              ? "border-brand-500 bg-brand-50"
              : "border-gray-300 bg-gray-50 hover:border-brand-400 hover:bg-brand-50/50"
          )}
        >
          <Upload
            size={32}
            className={clsx(
              "mb-3",
              dragActive ? "text-brand-600" : "text-gray-400"
            )}
          />
          <p className="mb-1 text-sm font-medium text-gray-700">
            Drag & drop your file here
          </p>
          <p className="text-xs text-gray-500">or click to browse (PDF, DOCX)</p>
          <input
            type="file"
            accept={accept}
            onChange={handleChange}
            className="hidden"
          />
        </label>
      ) : (
        <div className="flex items-center justify-between rounded-xl border border-gray-200 bg-gray-50 px-4 py-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-100 text-brand-600">
              <FileUp size={20} />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-900">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-500">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
          </div>
          <button
            onClick={clearFile}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-200 hover:text-gray-600"
          >
            <X size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
