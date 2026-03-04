// services/api.ts
// Base Axios instance wired to the FastAPI backend.

import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const api = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
    timeout: 120_000, // Deep mode can take a while
});

// Attach JWT token from sessionStorage before each request
api.interceptors.request.use((config) => {
    if (typeof window !== "undefined") {
        const token = sessionStorage.getItem("access_token");
        if (token) config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Auto-clear token on 401 (expired)
api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err?.response?.status === 401 && typeof window !== "undefined") {
            sessionStorage.removeItem("access_token");
            window.location.href = "/login";
        }
        return Promise.reject(err);
    }
);
