/**
 * Tests for the FileUpload component.
 */
import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  Upload: (props: any) => <svg data-testid="icon-upload" {...props} />,
  FileUp: (props: any) => <svg data-testid="icon-fileup" {...props} />,
  X: (props: any) => <svg data-testid="icon-x" {...props} />,
}));

import FileUpload from "@/components/FileUpload";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function createMockFile(
  name: string,
  type: string,
  size: number = 1024
): File {
  const buffer = new ArrayBuffer(size);
  return new File([buffer], name, { type });
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("FileUpload", () => {
  const mockOnFileSelect = jest.fn();

  beforeEach(() => {
    mockOnFileSelect.mockClear();
  });

  it("renders the drop zone", () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} />);
    expect(screen.getByText(/drag & drop/i)).toBeTruthy();
    expect(screen.getByText(/click to browse/i)).toBeTruthy();
  });

  it("renders upload icon in initial state", () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} />);
    expect(screen.getByTestId("icon-upload")).toBeTruthy();
  });

  it("accepts PDF files via input change", async () => {
    render(<FileUpload accept=".pdf,.docx" onFileSelect={mockOnFileSelect} />);

    const file = createMockFile("resume.pdf", "application/pdf");
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    expect(input).toBeTruthy();

    // Simulate file selection
    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledTimes(1);
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });

    // After selection, the file name should appear
    expect(screen.getByText("resume.pdf")).toBeTruthy();
  });

  it("calls onFileSelect callback with the file", async () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} />);

    const file = createMockFile("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document");
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);

    await waitFor(() => {
      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    });
  });

  it("shows file info after selection", async () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} />);

    const file = createMockFile("my_resume.pdf", "application/pdf", 2048);
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText("my_resume.pdf")).toBeTruthy();
      // File size display
      expect(screen.getByText(/KB/)).toBeTruthy();
    });
  });

  it("can clear selected file", async () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} />);

    const file = createMockFile("resume.pdf", "application/pdf");
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;

    Object.defineProperty(input, "files", { value: [file] });
    fireEvent.change(input);

    await waitFor(() => {
      expect(screen.getByText("resume.pdf")).toBeTruthy();
    });

    // Click the clear/X button
    const clearButton = screen.getByTestId("icon-x").closest("button");
    expect(clearButton).toBeTruthy();
    if (clearButton) {
      fireEvent.click(clearButton);
    }

    // Should return to the drop zone state
    await waitFor(() => {
      expect(screen.getByText(/drag & drop/i)).toBeTruthy();
    });
  });

  it("handles drag and drop", () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} />);

    const dropZone = screen.getByText(/drag & drop/i).closest("label");
    expect(dropZone).toBeTruthy();

    if (dropZone) {
      // Simulate drag over
      fireEvent.dragOver(dropZone, { preventDefault: jest.fn() });

      // Simulate drop with a file
      const file = createMockFile("dropped.pdf", "application/pdf");
      const dataTransfer = { files: [file] };
      fireEvent.drop(dropZone, {
        dataTransfer,
        preventDefault: jest.fn(),
      });

      expect(mockOnFileSelect).toHaveBeenCalledWith(file);
    }
  });
});
