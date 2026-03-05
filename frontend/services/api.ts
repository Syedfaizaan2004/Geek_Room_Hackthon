// services/api.ts
// Base Axios instance wired to the FastAPI backend.

import axios from "axios";
import { clearToken, getToken } from "./tokenStorage";

const LOCAL_DEFAULT_API_BASE = "http://localhost:8000/api/v1";

function normalizeApiBase(rawUrl?: string): string | null {
    if (!rawUrl) return null;

    let url = rawUrl.trim();
    if (!url) return null;

    // Render fromService.host gives a bare host; browsers require a scheme.
    if (!/^https?:\/\//i.test(url)) {
        url = `https://${url}`;
    }

    url = url.replace(/\/+$/, "");
    if (!/\/api\/v1$/i.test(url)) {
        url = `${url}/api/v1`;
    }

    return url;
}

function deriveRenderBackendFromFrontendHost(): string | null {
    if (typeof window === "undefined") return null;

    const { protocol, hostname } = window.location;
    if (!hostname.endsWith(".onrender.com")) return null;
    if (!hostname.includes("-frontend")) return null;

    const backendHost = hostname.replace("-frontend", "-backend");
    if (backendHost === hostname) return null;

    return `${protocol}//${backendHost}/api/v1`;
}

function deriveGenericBackendFromFrontendHost(): string | null {
    if (typeof window === "undefined") return null;

    const { protocol, hostname } = window.location;
    const candidates = [
        hostname.replace("-frontend", "-backend"),
        hostname.replace(/^frontend\./i, "backend."),
        hostname.replace(/^app\./i, "api."),
    ].filter((value, index, all) => value && value !== hostname && all.indexOf(value) === index);

    if (candidates.length === 0) return null;
    return `${protocol}//${candidates[0]}/api/v1`;
}

function deriveSameOriginApiBase(): string | null {
    if (typeof window === "undefined") return null;

    const { protocol, hostname, origin } = window.location;
    if (hostname === "localhost" || hostname === "127.0.0.1") {
        return `${protocol}//${hostname}:8000/api/v1`;
    }
    return `${origin}/api/v1`;
}

const API_BASE =
    normalizeApiBase(process.env.NEXT_PUBLIC_API_URL) ??
    normalizeApiBase(process.env.NEXT_PUBLIC_BACKEND_URL) ??
    deriveRenderBackendFromFrontendHost() ??
    deriveGenericBackendFromFrontendHost() ??
    deriveSameOriginApiBase() ??
    LOCAL_DEFAULT_API_BASE;

export const api = axios.create({
    baseURL: API_BASE,
    headers: { "Content-Type": "application/json" },
    timeout: 120_000, // Deep mode can take a while
});

// Attach JWT token before each request.
api.interceptors.request.use((config) => {
    const token = getToken();
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
});

// Auto-clear token on 401 (expired)
api.interceptors.response.use(
    (res) => res,
    (err) => {
        if (err?.response?.status === 401 && typeof window !== "undefined") {
            clearToken();
            window.location.href = "/login";
        }
        return Promise.reject(err);
    }
);
