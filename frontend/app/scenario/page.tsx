'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
    AlertTriangle,
    ArrowRight,
    BarChart3,
    Briefcase,
    CloudRain,
    Flame,
    Percent,
    TrendingDown,
} from 'lucide-react';

import DashboardLayout from '@/components/layout/DashboardLayout';
import SearchBar from '@/components/controls/SearchBar';
import { useCompanyIdentity } from '@/hooks/useCompanyIdentity';
import { ScenarioResponse, ScenarioType, runScenario } from '@/services/scenario';

const TYPES: ScenarioType[] = ['recession', 'inflation', 'rate_hike', 'growth_slowdown'];

const SCENARIO_META: Record<
    ScenarioType,
    { label: string; subtitle: string; icon: React.ReactNode; color: string; bg: string; border: string }
> = {
    recession: {
        label: 'Recession',
        subtitle: 'Demand slowdown and earnings pressure',
        icon: <CloudRain size={14} />,
        color: '#60a5fa',
        bg: 'rgba(96,165,250,0.14)',
        border: 'rgba(96,165,250,0.35)',
    },
    inflation: {
        label: 'Inflation',
        subtitle: 'Input cost spike and margin squeeze',
        icon: <Flame size={14} />,
        color: '#f59e0b',
        bg: 'rgba(245,158,11,0.14)',
        border: 'rgba(245,158,11,0.35)',
    },
    rate_hike: {
        label: 'Rate Hike',
        subtitle: 'Higher discount rates and debt cost',
        icon: <Percent size={14} />,
        color: '#f97316',
        bg: 'rgba(249,115,22,0.14)',
        border: 'rgba(249,115,22,0.35)',
    },
    growth_slowdown: {
        label: 'Growth Slowdown',
        subtitle: 'Topline deceleration stress',
        icon: <TrendingDown size={14} />,
        color: '#f43f5e',
        bg: 'rgba(244,63,94,0.14)',
        border: 'rgba(244,63,94,0.35)',
    },
};

function formatSignedNumber(value: number, digits: number): string {
    const prefix = value > 0 ? '+' : '';
    return `${prefix}${value.toFixed(digits)}`;
}

function deltaTone(value: number, positiveIsGood: boolean) {
    const good = positiveIsGood ? value >= 0 : value <= 0;
    return good ? '#10b981' : '#ef4444';
}

function ScenarioContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState(params.get('ticker') ?? '');
    const [type, setType] = useState<ScenarioType>((params.get('type') as ScenarioType) || 'recession');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [result, setResult] = useState<ScenarioResponse | null>(null);

    const activeTicker = (result?.ticker ?? ticker ?? '').toUpperCase();
    const { displayLabel } = useCompanyIdentity(activeTicker);

    const analyze = async (inputTicker: string, scenarioType: ScenarioType = type) => {
        const normalizedTicker = inputTicker.trim().toUpperCase();
        if (!normalizedTicker) return;

        setTicker(normalizedTicker);
        setLoading(true);
        setError('');
        try {
            const data = await runScenario(normalizedTicker, scenarioType);
            setResult(data);
        } catch {
            setError('Scenario analysis failed.');
            setResult(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const paramTicker = params.get('ticker');
        const scenarioType = (params.get('type') as ScenarioType) || 'recession';
        if (paramTicker) {
            setType(scenarioType);
            analyze(paramTicker, scenarioType);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const riskDelta = result ? result.adjusted_risk_score - result.baseline_risk_score : 0;
    const projectionDelta = result ? result.adjusted_projection - result.baseline_projection : 0;
    const activeMeta = SCENARIO_META[type];

    const generatedAt = useMemo(() => {
        if (!result?.generated_at) return '';
        const date = new Date(result.generated_at);
        if (Number.isNaN(date.getTime())) return '';
        return date.toLocaleString();
    }, [result?.generated_at]);

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center gap-3 mb-2">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(245,158,11,0.2)' }}>
                    <BarChart3 size={16} style={{ color: '#f59e0b' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Scenario Test</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        Deterministic macro stress testing for downside planning
                    </p>
                    {activeTicker && (
                        <p className="text-xs mt-1" style={{ color: '#fde68a' }}>
                            {displayLabel}
                        </p>
                    )}
                </div>
            </div>

            <SearchBar onAnalyze={(symbol) => analyze(symbol)} loading={loading} defaultValue={ticker} />

            <div className="card">
                <p className="text-xs font-semibold mb-3" style={{ color: 'var(--text-muted)' }}>SCENARIO TYPE</p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {TYPES.map((scenarioType) => {
                        const meta = SCENARIO_META[scenarioType];
                        const selected = type === scenarioType;
                        return (
                            <button
                                key={scenarioType}
                                onClick={() => {
                                    setType(scenarioType);
                                    if (ticker) analyze(ticker, scenarioType);
                                }}
                                className="rounded-xl p-3 text-left transition-all"
                                style={selected
                                    ? { background: meta.bg, border: `1px solid ${meta.border}` }
                                    : { background: 'var(--bg-primary)', border: '1px solid var(--border)' }}
                            >
                                <div className="flex items-center gap-2">
                                    <span style={{ color: meta.color }}>{meta.icon}</span>
                                    <span className="text-sm font-semibold text-white">{meta.label}</span>
                                </div>
                                <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                                    {meta.subtitle}
                                </p>
                            </button>
                        );
                    })}
                </div>
            </div>

            {error && (
                <div className="flex items-center gap-2 p-4 rounded-xl text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                    <AlertTriangle size={14} />
                    {error}
                </div>
            )}

            {loading && (
                <div className="space-y-3">
                    <div className="skeleton h-40 rounded-xl" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="skeleton h-28 rounded-xl" />
                        <div className="skeleton h-28 rounded-xl" />
                    </div>
                </div>
            )}

            {!loading && result && (
                <div className="space-y-4">
                    <div
                        className="card"
                        style={{
                            borderColor: activeMeta.border,
                            background: `linear-gradient(130deg, ${activeMeta.bg}, rgba(17,24,39,0.95) 42%)`,
                        }}
                    >
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                            <div>
                                <p className="text-xs uppercase tracking-wide" style={{ color: activeMeta.color }}>
                                    {activeMeta.label} Stress Output
                                </p>
                                <h2 className="text-lg font-semibold text-white mt-1">{displayLabel || activeTicker}</h2>
                                <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
                                    {generatedAt ? `Generated: ${generatedAt}` : 'Latest scenario output'}
                                </p>
                            </div>
                            {activeTicker && (
                                <div className="grid grid-cols-2 gap-2">
                                    <Link
                                        href={`/quick?ticker=${encodeURIComponent(activeTicker)}`}
                                        className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                        style={{ background: 'rgba(59,130,246,0.15)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.35)' }}
                                    >
                                        Quick
                                    </Link>
                                    <Link
                                        href={`/deep?ticker=${encodeURIComponent(activeTicker)}`}
                                        className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                        style={{ background: 'rgba(16,185,129,0.15)', color: '#86efac', border: '1px solid rgba(16,185,129,0.35)' }}
                                    >
                                        Deep
                                    </Link>
                                </div>
                            )}
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-4">
                            <Metric label="Baseline Projection" value={`$${result.baseline_projection.toFixed(2)}`} />
                            <Metric label="Adjusted Projection" value={`$${result.adjusted_projection.toFixed(2)}`} />
                            <Metric label="Baseline Risk" value={result.baseline_risk_score.toFixed(1)} />
                            <Metric label="Adjusted Risk" value={result.adjusted_risk_score.toFixed(1)} />
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mt-3">
                            <Metric
                                label="Projection Delta"
                                value={formatSignedNumber(projectionDelta, 2)}
                                color={deltaTone(projectionDelta, false)}
                            />
                            <Metric
                                label="Risk Delta"
                                value={formatSignedNumber(riskDelta, 2)}
                                color={deltaTone(riskDelta, false)}
                            />
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Impact Analysis</h3>
                            <p className="text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                {result.impact_analysis}
                            </p>
                            <div className="mt-4 rounded-lg p-3" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
                                <p className="text-xs font-semibold text-white mb-2">Scenario Link</p>
                                <Link
                                    href={`/compare?ticker=${encodeURIComponent(result.ticker)}`}
                                    className="inline-flex items-center gap-1 text-xs font-semibold"
                                    style={{ color: '#93c5fd' }}
                                >
                                    View peer comparison under current context
                                    <ArrowRight size={12} />
                                </Link>
                            </div>
                        </div>

                        <div className="card">
                            <div className="flex items-center gap-2 mb-3">
                                <Briefcase size={14} style={{ color: '#facc15' }} />
                                <h3 className="text-sm font-semibold text-white">Assumptions</h3>
                            </div>
                            {(result.assumptions?.length ?? 0) > 0 ? (
                                <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                    {result.assumptions.map((assumption, index) => (
                                        <p key={index}>- {assumption}</p>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    No assumptions were provided for this run.
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function Metric({ label, value, color }: { label: string; value: string; color?: string }) {
    return (
        <div className="rounded-lg p-3" style={{ background: 'rgba(15,23,42,0.7)', border: '1px solid var(--border)' }}>
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
