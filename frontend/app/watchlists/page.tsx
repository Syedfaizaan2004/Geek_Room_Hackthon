'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import {
    ArrowRight,
    BarChart3,
    Brain,
    Clock3,
    Search,
    ShieldAlert,
    Sparkles,
    Star,
    TrendingUp,
} from 'lucide-react';

import DashboardLayout from '@/components/layout/DashboardLayout';
import SearchBar from '@/components/controls/SearchBar';
import { useCompanyIdentity } from '@/hooks/useCompanyIdentity';
import { searchCompany } from '@/services/agent';
import { NextAction, RecommendationResponse, getRecommendations } from '@/services/recommendations';

function titleize(value?: string | null): string {
    if (!value) return 'Unknown';
    return value
        .replace(/_/g, ' ')
        .split(' ')
        .filter(Boolean)
        .map((word) => word[0].toUpperCase() + word.slice(1))
        .join(' ');
}

function actionUrl(ticker: string, type: string): string {
    const map: Record<string, string> = {
        peer_comparison: `/compare?ticker=${ticker}`,
        scenario_stress_test: `/scenario?ticker=${ticker}&type=recession`,
        hidden_risk_scan: `/risk?ticker=${ticker}`,
        growth_analysis: `/deep?ticker=${ticker}#growth-analysis`,
        fundamental_review: `/deep?ticker=${ticker}`,
        add_to_watchlist: `/watchlists?ticker=${ticker}`,
        deep_analysis: `/deep?ticker=${ticker}`,
    };
    return map[type] ?? `/quick?ticker=${ticker}`;
}

function actionIcon(type: string) {
    if (type === 'peer_comparison') return <BarChart3 size={14} style={{ color: '#60a5fa' }} />;
    if (type === 'scenario_stress_test' || type === 'hidden_risk_scan') return <ShieldAlert size={14} style={{ color: '#fca5a5' }} />;
    if (type === 'growth_analysis') return <TrendingUp size={14} style={{ color: '#86efac' }} />;
    if (type === 'deep_analysis' || type === 'fundamental_review') return <Brain size={14} style={{ color: '#c4b5fd' }} />;
    return <Search size={14} style={{ color: '#93c5fd' }} />;
}

function formatTimeLabel(timestamp?: string): string {
    if (!timestamp) return 'Not generated';
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return 'Not generated';
    return date.toLocaleString();
}

function RecommendationsContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState((params.get('ticker') ?? '').toUpperCase());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [data, setData] = useState<RecommendationResponse | null>(null);

    const run = async (inputTicker: string) => {
        const raw = inputTicker.trim();
        if (!raw) return;

        setLoading(true);
        setError('');

        try {
            let resolvedTicker = raw.toUpperCase();
            const looksLikeTicker = /^[A-Z][A-Z0-9.\-]{0,9}$/.test(resolvedTicker);

            if (!looksLikeTicker) {
                const company = await searchCompany(raw);
                if (!company?.ticker) {
                    setError('Ticker not found. Enter a valid stock ticker (e.g. MSFT).');
                    setData(null);
                    return;
                }
                resolvedTicker = company.ticker.toUpperCase();
            }

            setTicker(resolvedTicker);
            const response = await getRecommendations(resolvedTicker);
            setData(response);
        } catch {
            setError('Failed to fetch recommendations for this ticker.');
            setData(null);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const queryTicker = params.get('ticker');
        if (queryTicker) {
            run(queryTicker);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const activeTicker = (data?.ticker ?? ticker ?? '').toUpperCase();
    const { displayLabel } = useCompanyIdentity(activeTicker);
    const generatedLabel = useMemo(() => formatTimeLabel(data?.generated_at), [data?.generated_at]);

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(251,191,36,0.2)' }}>
                    <Star size={16} style={{ color: '#fbbf24' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Recommendations Hub</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        Personalized next steps, similar opportunities, and memory reminders
                    </p>
                    {activeTicker && (
                        <p className="text-xs mt-1" style={{ color: '#fde68a' }}>
                            {displayLabel}
                        </p>
                    )}
                </div>
            </div>

            <SearchBar
                onAnalyze={run}
                loading={loading}
                defaultValue={ticker}
                placeholder="Search company or enter ticker for recommendations..."
            />

            {error && (
                <div className="card text-sm" style={{ color: '#ef4444' }}>
                    {error}
                </div>
            )}

            {loading && (
                <div className="space-y-3">
                    <div className="skeleton h-36 rounded-xl" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="skeleton h-40 rounded-xl" />
                        <div className="skeleton h-40 rounded-xl" />
                    </div>
                </div>
            )}

            {data && !loading && (
                <div className="space-y-4">
                    <div
                        className="card"
                        style={{
                            borderColor: 'rgba(251,191,36,0.35)',
                            background: 'linear-gradient(130deg, rgba(251,191,36,0.15), rgba(17,24,39,0.95) 45%)',
                        }}
                    >
                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                            <div>
                                <p className="text-xs uppercase tracking-wide" style={{ color: '#fef08a' }}>
                                    Live Recommendation Snapshot
                                </p>
                                <h2 className="text-lg font-semibold text-white mt-1">{activeTicker}</h2>
                                <p className="text-sm mt-2" style={{ color: 'var(--text-primary)' }}>
                                    AI-ranked next moves based on memory and profile signals.
                                </p>
                            </div>
                            <div className="flex items-center gap-2 text-xs" style={{ color: '#fde68a' }}>
                                <Clock3 size={12} />
                                {generatedLabel}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4 text-xs">
                            <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                <p style={{ color: 'var(--text-muted)' }}>Next Actions</p>
                                <p className="text-white font-semibold">{data.next_actions?.length ?? 0}</p>
                            </div>
                            <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                <p style={{ color: 'var(--text-muted)' }}>Similar Companies</p>
                                <p className="text-white font-semibold">{data.similar_companies?.length ?? 0}</p>
                            </div>
                            <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                <p style={{ color: 'var(--text-muted)' }}>Reminders</p>
                                <p className="text-white font-semibold">{data.memory_reminders?.length ?? 0}</p>
                            </div>
                            <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                <p style={{ color: 'var(--text-muted)' }}>Watchlist Ideas</p>
                                <p className="text-white font-semibold">{data.watchlist_recommendations?.length ?? 0}</p>
                            </div>
                        </div>
                    </div>

                    <div className="card">
                        <div className="flex items-center gap-2 mb-3">
                            <Sparkles size={14} style={{ color: '#facc15' }} />
                            <h3 className="text-sm font-semibold text-white">Next Actions</h3>
                        </div>
                        {(data.next_actions ?? []).length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                {(data.next_actions ?? []).slice(0, 6).map((action: NextAction, idx) => (
                                    <Link
                                        key={`${action.action_type}-${idx}`}
                                        href={actionUrl(activeTicker, action.action_type)}
                                        className="rounded-xl p-3 border transition-all hover:translate-y-[-1px]"
                                        style={{ borderColor: 'var(--border)', background: 'rgba(15,23,42,0.65)' }}
                                    >
                                        <div className="flex items-center justify-between gap-2">
                                            <div className="flex items-center gap-2">
                                                {actionIcon(action.action_type)}
                                                <p className="text-xs font-semibold text-white">{titleize(action.action_type)}</p>
                                            </div>
                                            <ArrowRight size={12} style={{ color: 'var(--text-muted)' }} />
                                        </div>
                                        <p className="text-xs mt-2 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                            {action.explanation}
                                        </p>
                                    </Link>
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                No next actions available.
                            </p>
                        )}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Similar Companies</h3>
                            {(data.similar_companies ?? []).length > 0 ? (
                                <div className="space-y-3">
                                    {(data.similar_companies ?? []).slice(0, 8).map((company, idx) => (
                                        <div
                                            key={`${company.ticker}-${idx}`}
                                            className="rounded-xl p-3 border"
                                            style={{ borderColor: 'var(--border)', background: 'rgba(15,23,42,0.62)' }}
                                        >
                                            <div className="flex items-center justify-between gap-2">
                                                <p className="text-sm font-semibold text-white">{company.ticker}</p>
                                                <span className="badge badge-blue">
                                                    {(company.similarity_score * 100).toFixed(1)}% match
                                                </span>
                                            </div>
                                            <p className="text-xs mt-2 leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                                {company.reason}
                                            </p>
                                            <div className="grid grid-cols-2 gap-2 mt-3">
                                                <Link
                                                    href={`/quick?ticker=${encodeURIComponent(company.ticker)}`}
                                                    className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                                    style={{ background: 'rgba(59,130,246,0.15)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.35)' }}
                                                >
                                                    Quick
                                                </Link>
                                                <Link
                                                    href={`/deep?ticker=${encodeURIComponent(company.ticker)}`}
                                                    className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                                    style={{ background: 'rgba(16,185,129,0.15)', color: '#86efac', border: '1px solid rgba(16,185,129,0.35)' }}
                                                >
                                                    Deep
                                                </Link>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                    No similar companies found.
                                </p>
                            )}
                        </div>

                        <div className="space-y-4">
                            <div className="card">
                                <h3 className="text-sm font-semibold text-white mb-2">Memory Reminders</h3>
                                {(data.memory_reminders ?? []).length > 0 ? (
                                    <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                        {(data.memory_reminders ?? []).slice(0, 8).map((reminder, idx) => (
                                            <p key={idx}>- {reminder}</p>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                        No reminders available.
                                    </p>
                                )}
                            </div>

                            <div className="card">
                                <h3 className="text-sm font-semibold text-white mb-2">Behavioral Profile</h3>
                                <div className="flex flex-wrap gap-2 text-xs">
                                    {data.behavioral_profile?.dominant_sector && (
                                        <span className="badge badge-yellow">Sector: {titleize(data.behavioral_profile.dominant_sector)}</span>
                                    )}
                                    {data.behavioral_profile?.typical_risk_profile && (
                                        <span className="badge badge-red">Risk: {titleize(data.behavioral_profile.typical_risk_profile)}</span>
                                    )}
                                    {data.behavioral_profile?.analysis_mode_preference && (
                                        <span className="badge badge-green">Mode: {titleize(data.behavioral_profile.analysis_mode_preference)}</span>
                                    )}
                                    {data.behavioral_profile?.engagement_pattern && (
                                        <span className="badge badge-blue">Pattern: {titleize(data.behavioral_profile.engagement_pattern)}</span>
                                    )}
                                </div>
                                {!data.behavioral_profile && (
                                    <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>
                                        No behavioral profile available yet.
                                    </p>
                                )}
                            </div>

                            <div className="card">
                                <h3 className="text-sm font-semibold text-white mb-2">Watchlist Ideas</h3>
                                {(data.watchlist_recommendations ?? []).length > 0 ? (
                                    <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                        {(data.watchlist_recommendations ?? []).slice(0, 6).map((item, idx) => (
                                            <p key={`${item.ticker}-${idx}`}>
                                                <span className="text-white font-semibold">{item.ticker}</span>: {item.reason}
                                            </p>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                        No watchlist suggestions available.
                                    </p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default function WatchlistsPage() {
    return (
        <DashboardLayout>
            <Suspense fallback={<div className="max-w-3xl mx-auto skeleton h-40 rounded-xl" />}>
                <RecommendationsContent />
            </Suspense>
        </DashboardLayout>
    );
}
