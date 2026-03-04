import { api } from './api';

export type ScenarioType = 'recession' | 'inflation' | 'rate_hike' | 'growth_slowdown';

export interface ScenarioResponse {
    ticker: string;
    scenario_type: string;
    baseline_projection: number;
    adjusted_projection: number;
    baseline_risk_score: number;
    adjusted_risk_score: number;
    baseline_uncertainty_percent: number;
    adjusted_uncertainty_percent: number;
    impact_analysis: string;
    assumptions: string[];
    generated_at: string;
}

export async function runScenario(
    ticker: string,
    type: ScenarioType
): Promise<ScenarioResponse> {
    const res = await api.get<ScenarioResponse>(`/scenario/${ticker}`, { params: { type } });
    return res.data;
}
