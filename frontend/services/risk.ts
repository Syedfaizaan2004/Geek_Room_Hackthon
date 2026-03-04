import { api } from './api';

export interface RiskComponent {
    score: number;
    level?: string;
    explanation?: string;
}

export interface HiddenRisk {
    risk_name: string;
    severity: string;
    explanation: string;
}

export interface RiskResponse {
    ticker: string;
    composite_risk_score: number;
    risk_level: string;
    leverage_risk: RiskComponent;
    liquidity_risk: RiskComponent;
    earnings_risk: RiskComponent;
    cashflow_risk: RiskComponent;
    hidden_risks: HiddenRisk[];
    macro_sensitivity_notes: string;
    based_on_years: number;
    generated_at: string;
}

export async function getRiskProfile(ticker: string): Promise<RiskResponse> {
    const res = await api.get<RiskResponse>(`/risk/${ticker}`);
    return res.data;
}
