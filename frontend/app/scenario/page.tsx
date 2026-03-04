'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { BarChart3 } from 'lucide-react';
import SearchBar from '@/components/controls/SearchBar';
import { runScenario, ScenarioType, ScenarioResponse } from '@/services/scenario';

const TYPES: ScenarioType[] = ['recession', 'inflation', 'rate_hike', 'growth_slowdown'];

function ScenarioContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState(params.get('ticker') ?? '');
    const [type, setType] = useState<ScenarioType>((params.get('type') as ScenarioType) || 'recession');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<ScenarioResponse | null>(null);

    const analyze = async (inputTicker: string, scenarioType: ScenarioType = type) => {
        setTicker(inputTicker);
        setLoading(true);
        setError('');
        try {
            const data = await runScenario(inputTicker, scenarioType);
            setResult(data);
        } catch {
            setError('Scenario analysis failed.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const t = params.get('ticker');
        const scenarioType = (params.get('type') as ScenarioType) || 'recession';
        if (t) {
            setType(scenarioType);
            analyze(t, scenarioType);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const riskDelta = result ? result.adjusted_risk_score - result.baseline_risk_score : null;
    const projDelta = result ? result.adjusted_projection - result.baseline_projection : null;

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(245,158,11,0.2)' }}>
                    <BarChart3 size={16} style={{ color: '#f59e0b' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Scenario Test</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Run deterministic macro stress tests</p>
                </div>
            </div>

            <SearchBar onAnalyze={(t) => analyze(t)} loading={loading} defaultValue={ticker} />

            <div className="card">
                <p className="text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>SCENARIO TYPE</p>
                <div className="flex flex-wrap gap-2">
                    {TYPES.map((t) => (
                        <button
                            key={t}
                            onClick={() => {
                                setType(t);
                                if (ticker) analyze(ticker, t);
                            }}
                            className="px-3 py-1.5 rounded-lg text-xs capitalize"
                            style={type === t
                                ? { background: 'rgba(245,158,11,0.2)', color: '#f59e0b', border: '1px solid rgba(245,158,11,0.4)' }
                                : { background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                        >
                            {t.replace(/_/g, ' ')}
                        </button>
                    ))}
                </div>
            </div>

            {error && (
                <div className="card text-sm" style={{ color: '#ef4444' }}>
                    {error}
                </div>
            )}

            {loading && <div className="skeleton h-40 rounded-xl" />}

            {!loading && result && (
                <div className="space-y-4">
                    <div className="card">
                        <h3 className="text-sm font-semibold text-white mb-3 capitalize">{result.scenario_type.replace(/_/g, ' ')} impact</h3>
                        <div className="grid grid-cols-2 gap-3">
                            <Metric label="Baseline Projection" value={`$${result.baseline_projection.toFixed(2)}`} />
                            <Metric label="Adjusted Projection" value={`$${result.adjusted_projection.toFixed(2)}`} />
                            <Metric label="Baseline Risk" value={result.baseline_risk_score.toFixed(1)} />
                            <Metric label="Adjusted Risk" value={result.adjusted_risk_score.toFixed(1)} />
                        </div>
                        <div className="grid grid-cols-2 gap-3 mt-3">
                            <Metric
                                label="Projection Delta"
                                value={`${projDelta && projDelta > 0 ? '+' : ''}${(projDelta ?? 0).toFixed(2)}`}
                                color={(projDelta ?? 0) < 0 ? '#ef4444' : '#10b981'}
                            />
                            <Metric
                                label="Risk Delta"
                                value={`${riskDelta && riskDelta > 0 ? '+' : ''}${(riskDelta ?? 0).toFixed(2)}`}
                                color={(riskDelta ?? 0) > 0 ? '#ef4444' : '#10b981'}
                            />
                        </div>
                    </div>

                    <div className="card">
                        <h3 className="text-sm font-semibold text-white mb-2">Impact Analysis</h3>
                        <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                            {result.impact_analysis}
                        </p>
                        {(result.assumptions?.length ?? 0) > 0 && (
                            <div className="mt-3">
                                <p className="text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>Assumptions</p>
                                <div className="space-y-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                                    {result.assumptions.map((a, i) => <p key={i}>- {a}</p>)}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
    return (
        <div className="rounded-lg p-3" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{label}</p>
            <p className="text-sm font-semibold" style={{ color: color ?? 'white' }}>{value}</p>
        </div>
    );
}

export default function ScenarioPage() {
    return (
        <DashboardLayout>
            <Suspense fallback={<div className="max-w-3xl mx-auto skeleton h-40 rounded-xl" />}>
                <ScenarioContent />
            </Suspense>
        </DashboardLayout>
    );
}
