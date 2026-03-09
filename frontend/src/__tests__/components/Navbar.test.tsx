/**
 * Tests for the Navbar component.
 */
import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

// Mock next/navigation
jest.mock("next/navigation", () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    prefetch: jest.fn(),
  }),
  usePathname: () => "/dashboard",
}));

// Mock next/link
jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: any;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

// Mock lucide-react icons
jest.mock("lucide-react", () => ({
  FileText: (props: any) => <svg data-testid="icon-file-text" {...props} />,
  Briefcase: (props: any) => <svg data-testid="icon-briefcase" {...props} />,
  LayoutDashboard: (props: any) => (
    <svg data-testid="icon-dashboard" {...props} />
  ),
  Wand2: (props: any) => <svg data-testid="icon-wand" {...props} />,
  LogOut: (props: any) => <svg data-testid="icon-logout" {...props} />,
  Menu: (props: any) => <svg data-testid="icon-menu" {...props} />,
  X: (props: any) => <svg data-testid="icon-x" {...props} />,
}));

// Mock the zustand store
const mockLogout = jest.fn();
let mockUser: { name: string; email: string } | null = null;

jest.mock("@/lib/store", () => ({
  useAuthStore: () => ({
    user: mockUser,
    logout: mockLogout,
  }),
}));

import Navbar from "@/components/Navbar";

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("Navbar", () => {
  beforeEach(() => {
    mockUser = null;
    mockLogout.mockClear();
  });

  it("renders logo and title", () => {
    render(<Navbar />);
    expect(screen.getByText("Resume")).toBeTruthy();
    expect(screen.getByText("Helper")).toBeTruthy();
  });

  it("renders dashboard navigation links", () => {
    render(<Navbar />);
    expect(screen.getByText("Dashboard")).toBeTruthy();
    expect(screen.getByText("Resumes")).toBeTruthy();
    expect(screen.getByText("Jobs")).toBeTruthy();
    expect(screen.getByText("Tailor")).toBeTruthy();
  });

  it("shows user name when authenticated", () => {
    mockUser = { name: "Alice", email: "alice@example.com" };
    render(<Navbar />);
    expect(screen.getByText("Alice")).toBeTruthy();
  });

  it("calls logout handler on logout button click", () => {
    mockUser = { name: "Bob", email: "bob@example.com" };
    render(<Navbar />);

    const logoutButtons = screen.getAllByText("Logout");
    fireEvent.click(logoutButtons[0]);
    expect(mockLogout).toHaveBeenCalledTimes(1);
  });

  it("toggles mobile menu", () => {
    render(<Navbar />);

    // Mobile toggle button exists
    const menuButton = screen.getByTestId("icon-menu").closest("button");
    expect(menuButton).toBeTruthy();

    if (menuButton) {
      fireEvent.click(menuButton);
      // After click, the X icon should render (mobile menu open)
      expect(screen.getByTestId("icon-x")).toBeTruthy();
    }
  });
});
