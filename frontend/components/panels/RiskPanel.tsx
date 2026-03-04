'use client';
import { ShieldAlert, ShieldCheck, Shield } from 'lucide-react';

interface Props {
    data: {
        composite_risk_score?: number;
        risk_classification?: string;
        risk_level?: string;
        leverage_risk?: { score?: number };
        liquidity_risk?: { score?: number };
        earnings_risk?: { score?: number };
        cashflow_risk?: { score?: number };
        earnings_volatility_risk?: { score?: number };
        cashflow_instability_risk?: { score?: number };
        hidden_risks?: { risk_name?: string; severity?: string; explanation?: string }[];
        hidden_structural_risks?: string[];
    } | null;
    loading?: boolean;
}

const riskColor = (score: number) =>
    score >= 70 ? '#ef4444' : score >= 40 ? '#f59e0b' : '#10b981';

export default function RiskPanel({ data, loading }: Props) {
    if (loading) return <div className="card"><div className="skeleton h-40 rounded-lg" /></div>;
    if (!data) return null;

    const score = data.composite_risk_score ?? 0;
    const color = riskColor(score);
    const classification = data.risk_classification ?? data.risk_level ?? 'N/A';
    const Icon = score >= 70 ? ShieldAlert : score >= 40 ? Shield : ShieldCheck;

    const subRisks = [
        { label: 'Leverage', val: data.leverage_risk?.score ?? 0 },
        { label: 'Liquidity', val: data.liquidity_risk?.score ?? 0 },
        { label: 'Earnings Vol.', val: data.earnings_volatility_risk?.score ?? data.earnings_risk?.score ?? 0 },
        { label: 'Cash Flow', val: data.cashflow_instability_risk?.score ?? data.cashflow_risk?.score ?? 0 },
    ];

    const hiddenList = (data.hidden_structural_risks ?? []).length
        ? (data.hidden_structural_risks ?? [])
        : (data.hidden_risks ?? []).map((r) => r.risk_name || r.explanation || 'Unspecified hidden risk');

    return (
        <div className="card">
            <div className="flex items-center gap-2 mb-4">
                <Icon size={16} style={{ color }} />
                <h3 className="text-sm font-semibold text-white">Risk Analysis</h3>
                <span className="badge ml-auto" style={{ background: `${color}20`, color }}>
                    {classification}
                </span>
            </div>

            <div className="flex items-end gap-3 mb-4">
                <span className="text-4xl font-bold" style={{ color }}>{score.toFixed(0)}</span>
                <span className="text-sm pb-1" style={{ color: 'var(--text-muted)' }}>/100</span>
            </div>

            <div className="h-2 rounded-full mb-4" style={{ background: 'var(--bg-primary)' }}>
                <div className="h-2 rounded-full transition-all" style={{ width: `${score}%`, background: color }} />
            </div>

            <div className="grid grid-cols-2 gap-2">
                {subRisks.map(({ label, val }) => (
                    <div key={label} className="rounded-lg p-2.5" style={{ background: 'var(--bg-primary)' }}>
                        <div className="flex justify-between items-center mb-1">
                            <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</span>
                            <span className="text-xs font-medium" style={{ color: riskColor(val) }}>{val.toFixed(0)}</span>
                        </div>
                        <div className="h-1 rounded-full" style={{ background: 'var(--bg-card)' }}>
                            <div className="h-1 rounded-full" style={{ width: `${val}%`, background: riskColor(val) }} />
                        </div>
                    </div>
                ))}
            </div>

            {hiddenList.length > 0 && (
                <div className="mt-3 p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)' }}>
                    <p className="text-xs font-medium mb-1.5" style={{ color: '#ef4444' }}>Hidden Structural Risks</p>
                    {hiddenList.slice(0, 3).map((r, i) => (
                        <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>- {r}</p>
                    ))}
                </div>
            )}
        </div>
    );
}
