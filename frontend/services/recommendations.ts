// services/recommendations.ts
// Matches backend api/routes/recommendations.py and schemas/recommendations.py

import { api } from "./api";

export interface NextAction {
    action_type: string;
    explanation: string;
}

export interface SimilarCompany {
    ticker: string;
    similarity_score: number;
    reason: string;
}

export interface WatchlistRecommendation {
    ticker: string;
    reason: string;
}

export interface BehavioralProfile {
    dominant_sector?: string;
    typical_risk_profile?: string;
    analysis_mode_preference?: string;
    engagement_pattern?: string;
}

export interface RecommendationResponse {
    ticker: string;
    next_actions: NextAction[];
    similar_companies: SimilarCompany[];
    watchlist_recommendations: WatchlistRecommendation[];
    behavioral_profile?: BehavioralProfile;
    memory_reminders: string[];
    generated_at: string;
}

/** GET /api/v1/recommendations/{ticker} */
export async function getRecommendations(ticker: string): Promise<RecommendationResponse> {
    const res = await api.get<RecommendationResponse>(`/recommendations/${ticker}`);
    return res.data;
}
