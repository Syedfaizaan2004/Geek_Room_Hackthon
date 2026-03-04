// services/preferences.ts
// Preferences API service — matching backend PreferencesResponse/PreferencesUpdate schemas exactly.
// Backend field: risk_tolerance (NOT risk_profile)
// Backend sectors: stored lowercase

import { api } from "./api";

export interface PreferencesResponse {
    risk_tolerance: "conservative" | "moderate" | "aggressive";
    time_horizon: "short_term" | "medium_term" | "long_term";
    preferred_kpis: string[];
    preferred_sectors: string[];
    preferred_geographies: string[];
    updated_at: string;
}

export interface PreferencesUpdate {
    risk_tolerance?: "conservative" | "moderate" | "aggressive";
    time_horizon?: "short_term" | "medium_term" | "long_term";
    preferred_kpis?: string[];
    preferred_sectors?: string[];
    preferred_geographies?: string[];
}

/** GET /api/v1/preferences/me */
export async function fetchPreferences(): Promise<PreferencesResponse> {
    const res = await api.get<PreferencesResponse>("/preferences/me");
    return res.data;
}

/** PUT /api/v1/preferences/me */
export async function updatePreferences(
    update: PreferencesUpdate
): Promise<PreferencesResponse> {
    // Backend validator lowercases sectors/kpis — send them lowercase too.
    const payload: PreferencesUpdate = {
        ...update,
        preferred_sectors: update.preferred_sectors?.map((s) => s.toLowerCase()),
        preferred_kpis: update.preferred_kpis?.map((k) => k.toLowerCase()),
        preferred_geographies: update.preferred_geographies?.map((g) => g.toLowerCase()),
    };
    const res = await api.put<PreferencesResponse>("/preferences/me", payload);
    return res.data;
}
