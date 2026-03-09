import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const token = request.cookies.get("token")?.value;
  const authHeader = request.headers.get("authorization");
  const hasToken =
    !!token ||
    !!authHeader ||
    request.nextUrl.searchParams.has("token");

  // For client-side auth we check localStorage in components,
  // but middleware can gate based on a cookie fallback.
  // We still allow through — actual auth guard is client-side.
  const isAuthPage =
    request.nextUrl.pathname.startsWith("/login") ||
    request.nextUrl.pathname.startsWith("/register");
  const isDashboard = request.nextUrl.pathname.startsWith("/dashboard");

  // If accessing dashboard without cookie token, redirect to login
  // Note: primary auth is localStorage-based in the client
  if (isDashboard && !hasToken) {
    // Check for token in localStorage via a custom header won't work in middleware
    // So we allow through and let client-side handle redirect
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
