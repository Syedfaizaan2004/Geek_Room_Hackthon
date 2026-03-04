// services/memory.ts
import { api } from "./api";

export async function searchMemory(query: string, top_k = 5) {
    const res = await api.post("/memory/search", { query, top_k });
    return res.data;
}

export async function findSimilarCompanies(ticker: string, top_k = 5) {
    const res = await api.get(`/memory/similar/${ticker}`, { params: { top_k } });
    return res.data;
}

export async function getRiskPattern(threshold = 70) {
    const res = await api.get("/memory/risk-pattern", { params: { threshold } });
    return res.data;
}
