// store/authStore.ts
// Zustand global auth state — token stored in sessionStorage (not localStorage)

"use client";
import { create } from "zustand";
import { clearToken, getToken, saveToken } from "@/services/auth";

interface AuthState {
    token: string | null;
    isAuthenticated: boolean;
    login: (token: string) => void;
    logout: () => void;
    hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    token: null,
    isAuthenticated: false,

    login: (token: string) => {
        saveToken(token);
        set({ token, isAuthenticated: true });
    },

    logout: () => {
        clearToken();
        set({ token: null, isAuthenticated: false });
    },

    hydrate: () => {
        const token = getToken();
        set({ token, isAuthenticated: !!token });
    },
}));
