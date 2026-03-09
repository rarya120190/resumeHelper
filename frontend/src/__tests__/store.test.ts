/**
 * Tests for the Zustand auth store.
 */

// Mock the api module's getMe before importing store
jest.mock("@/lib/api", () => ({
  getMe: jest.fn(),
}));

import { act } from "@testing-library/react";

describe("useAuthStore", () => {
  beforeEach(() => {
    localStorage.clear();
    jest.resetModules();
  });

  async function getStore() {
    const { useAuthStore } = await import("@/lib/store");
    return useAuthStore;
  }

  it("has correct initial state when unauthenticated", async () => {
    const useAuthStore = await getStore();
    const state = useAuthStore.getState();

    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated()).toBe(false);
  });

  it("setToken stores token in state and localStorage", async () => {
    const useAuthStore = await getStore();

    act(() => {
      useAuthStore.getState().setToken("my-jwt-token");
    });

    const state = useAuthStore.getState();
    expect(state.token).toBe("my-jwt-token");
    expect(localStorage.getItem("token")).toBe("my-jwt-token");
    expect(state.isAuthenticated()).toBe(true);
  });

  it("setUser updates user in state", async () => {
    const useAuthStore = await getStore();
    const mockUser = { id: "u1", name: "Test User", email: "test@example.com" };

    act(() => {
      useAuthStore.getState().setUser(mockUser);
    });

    expect(useAuthStore.getState().user).toEqual(mockUser);
  });

  it("login flow: setToken + setUser", async () => {
    const useAuthStore = await getStore();

    act(() => {
      useAuthStore.getState().setToken("jwt-abc");
      useAuthStore.getState().setUser({
        id: "123",
        name: "Jane Doe",
        email: "jane@example.com",
      });
    });

    const state = useAuthStore.getState();
    expect(state.token).toBe("jwt-abc");
    expect(state.user?.name).toBe("Jane Doe");
    expect(state.isAuthenticated()).toBe(true);
  });

  it("logout clears user, token, and localStorage", async () => {
    const useAuthStore = await getStore();

    act(() => {
      useAuthStore.getState().setToken("jwt-abc");
      useAuthStore.getState().setUser({
        id: "1",
        name: "User",
        email: "u@e.com",
      });
    });

    act(() => {
      useAuthStore.getState().logout();
    });

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(localStorage.getItem("token")).toBeNull();
    expect(state.isAuthenticated()).toBe(false);
  });

  it("hydrate sets user from API when token exists", async () => {
    localStorage.setItem("token", "stored-jwt");

    const api = await import("@/lib/api");
    (api.getMe as jest.Mock).mockResolvedValue({
      id: "u1",
      name: "Hydrated User",
      email: "h@example.com",
    });

    const useAuthStore = await getStore();

    await act(async () => {
      await useAuthStore.getState().hydrate();
    });

    const state = useAuthStore.getState();
    expect(state.user?.name).toBe("Hydrated User");
    expect(state.isLoading).toBe(false);
  });

  it("hydrate clears state when API call fails", async () => {
    localStorage.setItem("token", "expired-jwt");

    const api = await import("@/lib/api");
    (api.getMe as jest.Mock).mockRejectedValue(new Error("401"));

    const useAuthStore = await getStore();

    await act(async () => {
      await useAuthStore.getState().hydrate();
    });

    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isLoading).toBe(false);
  });
});
