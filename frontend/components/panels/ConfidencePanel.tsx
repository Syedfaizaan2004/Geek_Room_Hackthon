'use client';
import { CheckCircle, AlertCircle, XCircle, Info } from 'lucide-react';

interface Props {
    data: {
        confidence_score?: number;
        confidence_classification?: string;
        data_completeness_pct?: number;
        contradictions?: { title?: string; description?: string; severity?: string }[];
        uncertainty?: { level?: string; factors?: string[] };
        assumptions?: string[];
    } | null;
    loading?: boolean;
}

const levelColor = (level?: string) =>
    level === 'high' ? '#10b981' : level === 'moderate' ? '#f59e0b' : '#ef4444';

export default function ConfidencePanel({ data, loading }: Props) {
    if (loading) return <div className="card"><div className="skeleton h-32 rounded-lg" /></div>;
    if (!data) return null;

    const score = data.confidence_score ?? 0;
    const cls = data.confidence_classification;
    const color = levelColor(cls);

    return (
        <div className="card">
            <div className="flex items-center gap-2 mb-4">
                <CheckCircle size={16} style={{ color }} />
                <h3 className="text-sm font-semibold text-white">Confidence & Transparency</h3>
            </div>

            <div className="grid grid-cols-2 gap-3 mb-4">
                <div className="rounded-lg p-3 text-center" style={{ background: 'var(--bg-primary)' }}>
                    <p className="text-3xl font-bold" style={{ color }}>{score.toFixed(0)}</p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>Confidence Score</p>
                    <span className="badge mt-1" style={{ background: `${color}20`, color }}>{cls ?? 'N/A'}</span>
                </div>
                <div className="rounded-lg p-3 text-center" style={{ background: 'var(--bg-primary)' }}>
                    <p className="text-3xl font-bold text-white">{data.data_completeness_pct?.toFixed(0) ?? '?'}%</p>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>Data Completeness</p>
                </div>
            </div>

            {/* Uncertainty */}
            {data.uncertainty && (
                <div className="p-3 rounded-lg mb-3" style={{ background: 'var(--bg-primary)' }}>
                    <div className="flex items-center gap-1.5 mb-1">
                        <Info size={12} style={{ color: 'var(--text-muted)' }} />
                        <span className="text-xs font-medium" style={{ color: 'var(--text-muted)' }}>Uncertainty: </span>
                        <span className="text-xs font-semibold" style={{ color: levelColor(data.uncertainty.level) }}>
                            {data.uncertainty.level?.toUpperCase()}
                        </span>
                    </div>
                    {data.uncertainty.factors?.slice(0, 2).map((f, i) => (
                        <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>• {f}</p>
                    ))}
                </div>
            )}

            {/* Contradictions */}
            {(data.contradictions?.length ?? 0) > 0 && (
                <div className="p-3 rounded-lg" style={{ background: 'rgba(239,68,68,0.05)', border: '1px solid rgba(239,68,68,0.2)' }}>
                    <div className="flex items-center gap-1.5 mb-1">
                        <AlertCircle size={12} style={{ color: '#ef4444' }} />
                        <span className="text-xs font-medium" style={{ color: '#ef4444' }}>
                            {data.contradictions!.length} Contradiction(s) Detected
                        </span>
                    </div>
                    {data.contradictions!.slice(0, 2).map((c, i) => (
                        <p key={i} className="text-xs" style={{ color: 'var(--text-muted)' }}>• {c.title}</p>
                    ))}
                </div>
            )}
        </div>
    );
}
