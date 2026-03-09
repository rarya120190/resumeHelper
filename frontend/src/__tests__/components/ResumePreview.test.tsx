/**
 * Tests for the ResumePreview component.
 */
import React from "react";
import { render, screen } from "@testing-library/react";

import ResumePreview from "@/components/ResumePreview";

// ---------------------------------------------------------------------------
// Test Data
// ---------------------------------------------------------------------------

const sampleSections = [
  {
    title: "Experience",
    items: [
      {
        text: "Built REST APIs using FastAPI serving 10k RPM",
        confidence: 0.95,
        modified: true,
      },
      {
        text: "Led a team of 5 engineers on cloud migration",
        confidence: 0.72,
        modified: true,
      },
      {
        text: "Original unmodified bullet point",
      },
    ],
  },
  {
    title: "Skills",
    items: [
      {
        text: "Python, FastAPI, PostgreSQL, Docker",
        confidence: 0.88,
        modified: true,
      },
      {
        text: "JavaScript, React, TypeScript",
      },
    ],
  },
];

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("ResumePreview", () => {
  it("renders section titles", () => {
    render(<ResumePreview sections={sampleSections} />);
    expect(screen.getByText("Experience")).toBeTruthy();
    expect(screen.getByText("Skills")).toBeTruthy();
  });

  it("renders all item text", () => {
    render(<ResumePreview sections={sampleSections} />);
    expect(
      screen.getByText("Built REST APIs using FastAPI serving 10k RPM")
    ).toBeTruthy();
    expect(
      screen.getByText("Led a team of 5 engineers on cloud migration")
    ).toBeTruthy();
    expect(
      screen.getByText("Original unmodified bullet point")
    ).toBeTruthy();
  });

  it("renders the Resume Preview header", () => {
    render(<ResumePreview sections={sampleSections} />);
    expect(screen.getByText("Resume Preview")).toBeTruthy();
  });

  it("shows confidence badges for modified items", () => {
    render(<ResumePreview sections={sampleSections} />);
    // 95% confidence badge
    expect(screen.getByText("95%")).toBeTruthy();
    // 72% confidence badge
    expect(screen.getByText("72%")).toBeTruthy();
    // 88% confidence badge
    expect(screen.getByText("88%")).toBeTruthy();
  });

  it("does not show confidence badge for unmodified items", () => {
    render(<ResumePreview sections={sampleSections} />);
    // The unmodified items should not have a percentage badge
    const unmodifiedItem = screen.getByText("Original unmodified bullet point");
    // Check that there's no sibling badge element
    const parentLi = unmodifiedItem.closest("li");
    expect(parentLi).toBeTruthy();
    // No percentage text inside this li
    expect(parentLi?.textContent).not.toMatch(/\d+%/);
  });

  it("applies green color class for high confidence (>= 0.9)", () => {
    render(<ResumePreview sections={sampleSections} />);
    const highConfItem = screen
      .getByText("Built REST APIs using FastAPI serving 10k RPM")
      .closest("li");
    expect(highConfItem?.className).toContain("green");
  });

  it("applies amber color class for medium confidence (0.7-0.89)", () => {
    render(<ResumePreview sections={sampleSections} />);
    const medConfItem = screen
      .getByText("Led a team of 5 engineers on cloud migration")
      .closest("li");
    expect(medConfItem?.className).toContain("amber");
  });

  it("renders empty state when no sections", () => {
    render(<ResumePreview sections={[]} />);
    expect(screen.getByText(/no resume content/i)).toBeTruthy();
  });

  it("shows confidence legend in header", () => {
    render(<ResumePreview sections={sampleSections} />);
    expect(screen.getByText("High confidence")).toBeTruthy();
    expect(screen.getByText("Medium")).toBeTruthy();
    expect(screen.getByText("Low")).toBeTruthy();
  });

  it("renders low confidence items with red/orange styling", () => {
    const lowConfSections = [
      {
        title: "Test",
        items: [
          {
            text: "A dubious claim",
            confidence: 0.3,
            modified: true,
          },
        ],
      },
    ];
    render(<ResumePreview sections={lowConfSections} />);
    const item = screen.getByText("A dubious claim").closest("li");
    expect(item?.className).toContain("red");
  });
});
