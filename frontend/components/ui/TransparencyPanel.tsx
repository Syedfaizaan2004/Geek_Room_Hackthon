// components/ui/TransparencyPanel.tsx
// Phase 17 — Collapsible assumptions & transparency panel.
// Shows model assumptions, contradictions, data completeness %.

'use client';
import { ChevronDown, AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface TransparencyPanelProps {
    confidence?: Record<string, unknown>;
    market?: Record<string, unknown>;
}

export default function TransparencyPanel({ confidence, market }: TransparencyPanelProps) {
    if (!confidence) return null;

    const completeness = (confidence.data_completeness_pct as number) ?? 0;
    const contradictions = (confidence.contradictions as Array<{ title?: string; severity?: string }>) ?? [];
    const uncertainty = confidence.uncertainty as { level?: string; factors?: string[] } | undefined;

    const ASSUMPTIONS = [
        'Market data sourced from yfinance (15-min delayed)',
        'Forecasts use moving averages and momentum indicators',
        'Risk scoring is deterministic — no LLM inference',
        'Fundamentals calculated from trailing twelve months (TTM)',
        'Peer comparison uses live sector data',
    ];

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
                        <span className="text-xs font-bold" style={{ color: completeness >= 80 ? '#10b981' : completeness >= 60 ? '#f59e0b' : '#ef4444' }}>
                            {Math.round(completeness)}%
                        </span>
                    </div>
                    <div className="h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.06)' }}>
                        <div className="h-full rounded-full transition-all duration-700"
                            style={{
                                width: `${completeness}%`,
                                background: completeness >= 80 ? '#10b981' : completeness >= 60 ? '#f59e0b' : '#ef4444'
                            }} />
                    </div>
                </div>

                {/* Assumptions list */}
                <div>
                    <p className="text-[10px] font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>ASSUMPTIONS</p>
                    <ul className="space-y-1.5">
                        {ASSUMPTIONS.map((a, i) => (
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
                                <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg"
                                    style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}>
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
                {uncertainty?.factors && uncertainty.factors.length > 0 && (
                    <div>
                        <p className="text-[10px] font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>UNCERTAINTY FACTORS</p>
                        <div className="flex flex-wrap gap-2">
                            {uncertainty.factors.map((f, i) => (
                                <span key={i} className="text-[11px] px-2 py-1 rounded-lg"
                                    style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}>
                                    {f}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </details>
    );
}
