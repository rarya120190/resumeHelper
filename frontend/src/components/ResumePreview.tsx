"use client";

import clsx from "clsx";

interface Section {
  title: string;
  items: {
    text: string;
    confidence?: number; // 0-1, undefined means original/unmodified
    modified?: boolean;
  }[];
}

interface ResumePreviewProps {
  sections: Section[];
  className?: string;
}

function confidenceColor(confidence: number): string {
  if (confidence >= 0.9) return "bg-green-100 border-green-300";
  if (confidence >= 0.7) return "bg-amber-100 border-amber-300";
  if (confidence >= 0.5) return "bg-orange-100 border-orange-300";
  return "bg-red-100 border-red-300";
}

function confidenceBadge(confidence: number): string {
  if (confidence >= 0.9) return "text-green-700 bg-green-50";
  if (confidence >= 0.7) return "text-amber-700 bg-amber-50";
  if (confidence >= 0.5) return "text-orange-700 bg-orange-50";
  return "text-red-700 bg-red-50";
}

export default function ResumePreview({
  sections,
  className,
}: ResumePreviewProps) {
  return (
    <div
      className={clsx(
        "mx-auto max-w-3xl rounded-xl border border-gray-200 bg-white shadow-sm",
        className
      )}
    >
      {/* Header */}
      <div className="border-b border-gray-100 px-6 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            Resume Preview
          </h3>
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded border border-green-300 bg-green-100" />
              High confidence
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded border border-amber-300 bg-amber-100" />
              Medium
            </span>
            <span className="flex items-center gap-1">
              <span className="inline-block h-3 w-3 rounded border border-red-300 bg-red-100" />
              Low
            </span>
          </div>
        </div>
      </div>

      {/* Body */}
      <div className="space-y-6 p-6">
        {sections.map((section, si) => (
          <div key={si}>
            <h4 className="mb-2 text-sm font-bold uppercase tracking-wider text-brand-700">
              {section.title}
            </h4>
            <ul className="space-y-1.5">
              {section.items.map((item, ii) => (
                <li
                  key={ii}
                  className={clsx(
                    "rounded-md px-3 py-2 text-sm leading-relaxed",
                    item.modified && item.confidence !== undefined
                      ? `border-l-4 ${confidenceColor(item.confidence)}`
                      : "text-gray-700"
                  )}
                >
                  <span>{item.text}</span>
                  {item.modified && item.confidence !== undefined && (
                    <span
                      className={clsx(
                        "ml-2 inline-block rounded-full px-2 py-0.5 text-[10px] font-semibold",
                        confidenceBadge(item.confidence)
                      )}
                    >
                      {Math.round(item.confidence * 100)}%
                    </span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}

        {sections.length === 0 && (
          <p className="py-12 text-center text-sm text-gray-400">
            No resume content to preview yet. Tailor a resume to see results.
          </p>
        )}
      </div>
    </div>
  );
}
