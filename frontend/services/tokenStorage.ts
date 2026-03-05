const TOKEN_KEY = "access_token";

export function saveToken(token: string) {
    if (typeof window === "undefined") return;
    try {
        localStorage.setItem(TOKEN_KEY, token);
        // Migrate from older session-based storage.
        sessionStorage.removeItem(TOKEN_KEY);
    } catch {
        // Ignore storage errors (private mode/quota).
    }
}

export function clearToken() {
    if (typeof window === "undefined") return;
    try {
        localStorage.removeItem(TOKEN_KEY);
        sessionStorage.removeItem(TOKEN_KEY);
    } catch {
        // Ignore storage errors.
    }
}

export function getToken(): string | null {
    if (typeof window === "undefined") return null;
    try {
        const localToken = localStorage.getItem(TOKEN_KEY);
        if (localToken) return localToken;

        // Backward-compatible read and one-time migration.
        const sessionToken = sessionStorage.getItem(TOKEN_KEY);
        if (sessionToken) {
            localStorage.setItem(TOKEN_KEY, sessionToken);
            sessionStorage.removeItem(TOKEN_KEY);
        }
        return sessionToken;
    } catch {
        return null;
    }
}
