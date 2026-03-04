'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import SearchBar from '@/components/controls/SearchBar';
import { runAnalysis, AgentResponseData } from '@/services/agent';
import { GitCompare, AlertTriangle } from 'lucide-react';

type ComparisonData = {
    ticker?: string;
    peers?: string[];
    valuation_comparison?: Record<string, string>;
    profitability_comparison?: Record<string, string | number>;
    growth_comparison?: Record<string, string>;
    risk_comparison?: Record<string, string | number>;
    financial_health_position?: string;
    strengths?: string[];
    weaknesses?: string[];
    strategic_summary?: string;
};

function CompareContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState(params.get('ticker') ?? '');
    const [data, setData] = useState<AgentResponseData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const analyze = async (inputTicker: string) => {
        setTicker(inputTicker);
        setError('');
        setLoading(true);
        try {
            const res = await runAnalysis(inputTicker, 'compare');
            setData(res.data);
        } catch {
            setError('Comparison analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const t = params.get('ticker');
        if (t) {
            analyze(t);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const comparison = (data?.comparison as ComparisonData | undefined) ?? null;

    return (
        <div className="max-w-4xl mx-auto space-y-6">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(16,185,129,0.2)' }}>
                    <GitCompare size={16} style={{ color: '#10b981' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Peer Comparison</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Benchmark competitors with deterministic valuation, growth, and risk ranks</p>
                </div>
            </div>

            <SearchBar onAnalyze={analyze} loading={loading} defaultValue={ticker} />

            {error && (
                <div className="flex items-center gap-2 p-4 rounded-xl text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                    <AlertTriangle size={14} />
                    {error}
                </div>
            )}

            {loading && <div className="skeleton h-48 rounded-xl" />}

            {comparison && !loading && (
                <div className="space-y-4">
                    <div className="card">
                        <h3 className="text-sm font-semibold text-white mb-2">Strategic Summary</h3>
                        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                            {comparison.strategic_summary ?? 'No strategic summary available.'}
                        </p>
                        {(comparison.peers?.length ?? 0) > 0 && (
                            <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
                                Peers: {comparison.peers?.join(', ')}
                            </p>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Valuation & Growth</h3>
                            <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                <p>P/E: {comparison.valuation_comparison?.pe_status ?? 'N/A'}</p>
                                <p>P/B: {comparison.valuation_comparison?.pb_status ?? 'N/A'}</p>
                                <p>EV/EBITDA: {comparison.valuation_comparison?.ev_ebitda_status ?? 'N/A'}</p>
                                <p>Revenue Growth: {comparison.growth_comparison?.revenue_growth_position ?? 'N/A'}</p>
                                <p>Earnings Growth: {comparison.growth_comparison?.earnings_growth_position ?? 'N/A'}</p>
                            </div>
                        </div>

                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Profitability & Risk</h3>
                            <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                <p>ROE Rank: #{comparison.profitability_comparison?.roe_rank ?? 'N/A'}</p>
                                <p>Margin Position: {comparison.profitability_comparison?.margin_position ?? 'N/A'}</p>
                                <p>Risk Rank: #{comparison.risk_comparison?.relative_risk_rank ?? 'N/A'}</p>
                                <p>Safety Position: {comparison.risk_comparison?.safety_position ?? 'N/A'}</p>
                                <p>Health Position: {comparison.financial_health_position ?? 'N/A'}</p>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Strengths</h3>
                            <div className="space-y-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                                {(comparison.strengths ?? []).slice(0, 5).map((item, idx) => (
                                    <p key={idx}>- {item}</p>
                                ))}
                            </div>
                        </div>

                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Weaknesses</h3>
                            <div className="space-y-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                                {(comparison.weaknesses ?? []).slice(0, 5).map((item, idx) => (
                                    <p key={idx}>- {item}</p>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function ComparePage() {
    return (
        <DashboardLayout>
            <Suspense fallback={<div className="max-w-4xl mx-auto skeleton h-40 rounded-xl" />}>
                <CompareContent />
            </Suspense>
        </DashboardLayout>
    );
}
