// components/ui/TransparencyPanel.tsx
// Collapsible assumptions and transparency panel.

'use client';
import { ChevronDown, AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface TransparencyPanelProps {
    confidence?: Record<string, unknown>;
    market?: Record<string, unknown>;
}

export default function TransparencyPanel({ confidence }: TransparencyPanelProps) {
    if (!confidence) return null;

    const completenessRaw =
        (confidence.data_completeness_pct as number | undefined) ??
        (confidence.completeness_score as number | undefined);
    const completeness = typeof completenessRaw === 'number' ? completenessRaw : 0;

    const contradictionRows = (confidence.contradictions as Array<Record<string, unknown>> | undefined) ?? [];
    const contradictions = contradictionRows.map((c) => ({
        title:
            (c.title as string | undefined) ??
            (c.explanation as string | undefined) ??
            (c.type as string | undefined) ??
            'Potential data inconsistency detected',
        severity: c.severity as string | undefined,
    }));

    const uncertainty = confidence.uncertainty as
        | { level?: string; factors?: string[]; drivers?: string[] }
        | undefined;
    const uncertaintyFactors = uncertainty?.factors ?? uncertainty?.drivers ?? [];
    const uncertaintyLevel = uncertainty?.level ?? 'low';

    const defaultAssumptions = [
        'Market data sourced from yfinance (15-min delayed)',
        'Forecasts use moving averages and momentum indicators',
        'Risk scoring is deterministic - no LLM inference',
        'Fundamentals calculated from trailing twelve months (TTM)',
        'Peer comparison uses live sector data',
    ];
    const assumptionsFromApi = Array.isArray(confidence.assumptions)
        ? confidence.assumptions.filter((x): x is string => typeof x === 'string' && x.trim().length > 0)
        : [];
    const assumptions = assumptionsFromApi.length > 0 ? assumptionsFromApi : defaultAssumptions;

    return (
        <details className="card details-panel fade-in">
            <summary className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center gap-2">
                    <Info size={14} style={{ color: '#6366f1' }} />
                    <h3 className="text-sm font-semibold text-white">Model Assumptions &amp; Transparency</h3>
                </div>
                <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} className="chev" />
            </summary>

            <div className="mt-4 space-y-4">
                {/* Data Completeness */}
                <div>
                    <div className="flex justify-between items-center mb-1.5">
                        <span className="text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>DATA COMPLETENESS</span>
                        <span
                            className="text-xs font-bold"
                            style={{ color: completeness >= 80 ? '#10b981' : completeness >= 60 ? '#f59e0b' : '#ef4444' }}
                        >
                            {Math.round(completeness)}%
                        </span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <div
                            className="h-full rounded-full transition-all duration-700"
                            style={{
                                width: `${completeness}%`,
                                background: completeness >= 80 ? '#10b981' : completeness >= 60 ? '#f59e0b' : '#ef4444',
                            }}
                        />
                    </div>
                </div>

                {/* Assumptions list */}
                <div>
                    <p className="text-[10px] font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>ASSUMPTIONS</p>
                    <ul className="space-y-1.5">
                        {assumptions.map((a, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs" style={{ color: 'rgba(255,255,255,0.55)' }}>
                                <CheckCircle size={11} style={{ color: '#10b981', flexShrink: 0, marginTop: 1 }} />
                                {a}
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Contradictions */}
                {contradictions.length > 0 && (
                    <div>
                        <p className="text-[10px] font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>CONTRADICTION ALERTS</p>
                        <div className="space-y-1.5">
                            {contradictions.map((c, i) => (
                                <div
                                    key={i}
                                    className="flex items-start gap-2 px-3 py-2 rounded-lg"
                                    style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}
                                >
                                    <AlertTriangle size={11} style={{ color: '#f59e0b', flexShrink: 0, marginTop: 1 }} />
                                    <span className="text-xs" style={{ color: '#fbbf24' }}>
                                        {c.title ?? 'Potential data inconsistency detected'}
                                        {c.severity && <span className="ml-1 opacity-60">({c.severity})</span>}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Uncertainty */}
                <div>
                    <div className="flex items-center justify-between mb-2">
                        <p className="text-[10px] font-semibold" style={{ color: 'var(--text-muted)' }}>UNCERTAINTY FACTORS</p>
                        <span
                            className="text-[10px] font-bold uppercase"
                            style={{
                                color:
                                    uncertaintyLevel === 'high'
                                        ? '#ef4444'
                                        : uncertaintyLevel === 'moderate'
                                            ? '#f59e0b'
                                            : '#10b981',
                            }}
                        >
                            {uncertaintyLevel}
                        </span>
                    </div>
                    {uncertaintyFactors.length > 0 ? (
                        <div className="flex flex-wrap gap-2">
                            {uncertaintyFactors.map((f, i) => (
                                <span
                                    key={i}
                                    className="text-[11px] px-2 py-1 rounded-lg"
                                    style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                                >
                                    {f}
                                </span>
                            ))}
                        </div>
                    ) : (
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            No major uncertainty drivers detected for current inputs.
                        </p>
                    )}
                </div>
            </div>
        </details>
    );
}
