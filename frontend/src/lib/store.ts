import { create } from "zustand";
import { getMe } from "./api";

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  setToken: (token: string) => void;
  setUser: (user: User) => void;
  logout: () => void;
  hydrate: () => Promise<void>;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  token: typeof window !== "undefined" ? localStorage.getItem("token") : null,
  isLoading: true,

  setToken: (token: string) => {
    localStorage.setItem("token", token);
    set({ token });
  },

  setUser: (user: User) => set({ user }),

  logout: () => {
    localStorage.removeItem("token");
    set({ user: null, token: null });
  },

  hydrate: async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      set({ isLoading: false });
      return;
    }
    try {
      set({ token });
      const user = await getMe();
      set({ user, isLoading: false });
    } catch {
      localStorage.removeItem("token");
      set({ user: null, token: null, isLoading: false });
    }
  },

  isAuthenticated: () => !!get().token,
}));
