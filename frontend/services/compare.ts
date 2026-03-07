import { api } from "./api";

export interface ValuationComparison {
    pe_status: string;
    pb_status: string;
    ev_ebitda_status: string;
    target_pe?: number | null;
    peer_avg_pe?: number | null;
    target_pb?: number | null;
    peer_avg_pb?: number | null;
    target_ev_ebitda?: number | null;
    peer_avg_ev_ebitda?: number | null;
}

export interface ProfitabilityComparison {
    roe_rank: number;
    margin_position: string;
    target_roe?: number | null;
    peer_avg_roe?: number | null;
    target_net_margin?: number | null;
    peer_avg_net_margin?: number | null;
    peer_count?: number;
}

export interface GrowthComparison {
    revenue_growth_position: string;
    earnings_growth_position: string;
    target_revenue_growth?: number | null;
    peer_avg_revenue_growth?: number | null;
    target_earnings_growth?: number | null;
    peer_avg_earnings_growth?: number | null;
}

export interface RiskComparison {
    relative_risk_rank: number;
    safety_position: string;
    target_risk_score?: number | null;
    peer_avg_risk_score?: number | null;
    universe_size?: number;
}

export interface PeerSnapshot {
    ticker: string;
    financial_health_score?: number | null;
    financial_health_classification?: string;
    composite_risk_score?: number | null;
    roe?: number | null;
    net_profit_margin?: number | null;
    revenue_growth_yoy?: number | null;
    earnings_growth_yoy?: number | null;
}

export interface ComparisonResponse {
    ticker: string;
    peers: string[];
    valuation_comparison: ValuationComparison;
    profitability_comparison: ProfitabilityComparison;
    growth_comparison: GrowthComparison;
    risk_comparison: RiskComparison;
    financial_health_position: string;
    strengths: string[];
    weaknesses: string[];
    strategic_summary: string;
    comparison_universe_size?: number;
    target_snapshot?: PeerSnapshot | null;
    peer_snapshots?: PeerSnapshot[];
    generated_at: string;
}

export async function getPeerComparison(ticker: string, peers?: string[]): Promise<ComparisonResponse> {
    const params = peers && peers.length > 0 ? { peers: peers.join(",") } : undefined;
    const res = await api.get<ComparisonResponse>(`/compare/${ticker}`, { params });
    return res.data;
}
