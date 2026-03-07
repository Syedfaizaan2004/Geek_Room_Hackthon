// services/memory.ts
import { api } from "./api";

export interface MemorySimilarResult {
    ticker: string;
    similarity_score: number;
    summary_excerpt: string;
    risk_score: number;
    financial_health_score: number;
    insight_type: string;
    stored_at?: string | null;
}

export interface MemorySearchResponse {
    query: string;
    similar_results: MemorySimilarResult[];
    total_found: number;
}

export interface MemoryRecentResult {
    ticker: string;
    summary_excerpt: string;
    risk_score: number;
    financial_health_score: number;
    insight_type: string;
    stored_at?: string | null;
}

export async function searchMemory(query: string, top_k = 5): Promise<MemorySearchResponse> {
    const res = await api.post<MemorySearchResponse>("/memory/search", { query, top_k });
    return res.data;
}

export async function findSimilarCompanies(ticker: string, top_k = 5): Promise<MemorySearchResponse> {
    const res = await api.get<MemorySearchResponse>(`/memory/similar/${ticker}`, { params: { top_k } });
    return res.data;
}

export async function getRiskPattern(threshold = 70) {
    const res = await api.get("/memory/risk-pattern", { params: { threshold } });
    return res.data;
}

export async function getRecentMemory(limit = 20): Promise<MemoryRecentResult[]> {
    const res = await api.get<MemoryRecentResult[]>("/memory/recent", { params: { limit } });
    return res.data;
}
