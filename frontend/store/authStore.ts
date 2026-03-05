"use client";
import { create } from "zustand";
import { clearToken, getToken, saveToken } from "@/services/tokenStorage";

interface AuthState {
    token: string | null;
    isAuthenticated: boolean;
    hydrated: boolean;
    login: (token: string) => void;
    logout: () => void;
    hydrate: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    token: null,
    isAuthenticated: false,
    hydrated: false,

    login: (token: string) => {
        saveToken(token);
        set({ token, isAuthenticated: true, hydrated: true });
    },

    logout: () => {
        clearToken();
        set({ token: null, isAuthenticated: false, hydrated: true });
    },

    hydrate: () => {
        const token = getToken();
        set({ token, isAuthenticated: !!token, hydrated: true });
    },
}));
