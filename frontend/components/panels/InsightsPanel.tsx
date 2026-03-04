'use client';
import { TrendingUp, TrendingDown, Lightbulb } from 'lucide-react';

interface Props {
    data: {
        executive_summary?: string;
        strengths?: string[];
        risks?: string[];
        bull_thesis?: string[];
        bear_thesis?: string[];
        plain_language_summary?: string;
        llm_enhancement?: { enhanced_text?: string; llm_used?: boolean; provider?: string };
    } | null;
    loading?: boolean;
}

export default function InsightsPanel({ data, loading }: Props) {
    if (loading) return (
        <div className="card space-y-3">
            <div className="skeleton h-4 w-32" />
            <div className="skeleton h-24 rounded-lg" />
            <div className="skeleton h-16 rounded-lg" />
        </div>
    );
    if (!data) return null;

    const llm = data.llm_enhancement;
    const displayText = llm?.llm_used ? llm.enhanced_text : data.plain_language_summary;

    return (
        <div className="card space-y-4">
            <div className="flex items-center gap-2">
                <Lightbulb size={16} style={{ color: '#f59e0b' }} />
                <h3 className="text-sm font-semibold text-white">Insights & Analysis</h3>
                {llm?.llm_used && (
                    <span className="badge badge-blue ml-auto">✨ AI Enhanced ({llm.provider})</span>
                )}
            </div>

            {/* Summary */}
            {data.executive_summary && (
                <div className="p-3 rounded-lg" style={{ background: 'var(--bg-primary)' }}>
                    <p className="text-xs font-semibold mb-1.5" style={{ color: 'var(--text-muted)' }}>EXECUTIVE SUMMARY</p>
                    <p className="text-sm text-white leading-relaxed">{data.executive_summary}</p>
                </div>
            )}

            {/* Bull vs Bear */}
            <div className="grid grid-cols-2 gap-3">
                <div className="p-3 rounded-lg" style={{ background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)' }}>
                    <div className="flex items-center gap-1.5 mb-2">
                        <TrendingUp size={12} style={{ color: '#10b981' }} />
                        <span className="text-xs font-medium" style={{ color: '#10b981' }}>Bull Thesis</span>
                    </div>
                    {data.bull_thesis?.slice(0, 3).map((b, i) => (
                        <p key={i} className="text-xs mb-0.5" style={{ color: 'var(--text-muted)' }}>• {b}</p>
                    ))}
                </div>
                <div className="p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)' }}>
                    <div className="flex items-center gap-1.5 mb-2">
                        <TrendingDown size={12} style={{ color: '#ef4444' }} />
                        <span className="text-xs font-medium" style={{ color: '#ef4444' }}>Bear Thesis</span>
                    </div>
                    {data.bear_thesis?.slice(0, 3).map((b, i) => (
                        <p key={i} className="text-xs mb-0.5" style={{ color: 'var(--text-muted)' }}>• {b}</p>
                    ))}
                </div>
            </div>

            {/* Plain language or LLM enhanced */}
            {displayText && (
                <div className="p-3 rounded-lg" style={{ background: 'var(--bg-primary)' }}>
                    <p className="text-xs font-semibold mb-1.5" style={{ color: 'var(--text-muted)' }}>
                        {llm?.llm_used ? 'AI NARRATIVE' : 'PLAIN SUMMARY'}
                    </p>
                    <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>{displayText}</p>
                </div>
            )}
        </div>
    );
}
