// services/agent.ts
// Matches backend schemas/agent.py exactly.
// AgentResponse: { ticker, mode, summary_type, data: AgentResponseData, execution_time_ms, generated_at }
// AgentResponseData: { market, forecast, fundamentals, risk, comparison, scenario, insights, confidence, llm_enhanced_memo, next_step_recommendation }

import { api } from "./api";

export type AnalysisMode = "quick" | "deep" | "compare" | "hidden_risk" | "next_analysis";

export interface AgentResponseData {
    market?: Record<string, unknown>;
    forecast?: Record<string, unknown>;
    fundamentals?: Record<string, unknown>;
    risk?: Record<string, unknown>;
    comparison?: Record<string, unknown>;
    scenario?: Record<string, unknown> | Record<string, unknown>[];
    insights?: Record<string, unknown>;
    confidence?: Record<string, unknown>;
    llm_enhanced_memo?: Record<string, unknown>;
    next_step_recommendation?: string;
    recommendations?: Record<string, unknown>;    // Phase 15
    memory_recall?: Record<string, unknown>[];    // Phase 12
    demo_mode?: boolean;
    demo_note?: string;
}

export interface AgentResponse {
    ticker: string;
    mode: string;
    summary_type: string;
    data: AgentResponseData;
    execution_time_ms: number;
    generated_at: string;
}

/**
 * POST /api/v1/analyze
 * Runs the LangGraph orchestration pipeline.
 * Returns AgentResponse typed correctly.
 */
export async function runAnalysis(
    ticker: string,
    mode: AnalysisMode
): Promise<AgentResponse> {
    const res = await api.post<AgentResponse>("/analyze", { ticker, mode });
    return res.data;
}

/**
 * GET /api/v1/suggest-company?q=...
 * Search company name to get ticker suggestions.
 */
export async function suggestCompany(query: string): Promise<{ ticker: string; company_name: string }[]> {
    try {
        const res = await api.get<{ suggestions: { ticker: string; company_name: string }[] }>(`/suggest-company?q=${encodeURIComponent(query)}`);
        return res.data?.suggestions || [];
    } catch {
        return [];
    }
}

/**
 * GET /api/v1/search-company?q=...
 * Resolve a company name into a ticker.
 */
export async function searchCompany(query: string): Promise<{ ticker: string; company_name: string } | null> {
    try {
        const res = await api.get<{ ticker: string; company_name: string }>(`/search-company?q=${encodeURIComponent(query)}`);
        return res.data ?? null;
    } catch {
        return null;
    }
}

/**
 * GET /api/v1/resolve-ticker?q=...
 * Resolve ticker symbol to company name.
 */
export async function resolveTicker(ticker: string): Promise<{ ticker: string; company_name: string } | null> {
    try {
        const res = await api.get<{ ticker: string; company_name: string }>(`/resolve-ticker?q=${encodeURIComponent(ticker)}`);
        return res.data ?? null;
    } catch {
        return null;
    }
}

/**
 * POST /api/v1/ai-insights
 * Generate AI Insights for deep mode
 */
export async function getAIInsights(ticker: string, analysis: Record<string, unknown>): Promise<{ insights: { question: string; answer: string }[], llm_used: boolean, provider: string }> {
    const res = await api.post('/ai-insights', { ticker, analysis });
    return res.data;
}
