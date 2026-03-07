'use client';

import { Suspense, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { AlertTriangle, BarChart3, GitCompare, Shield, Target, Users } from 'lucide-react';

import DashboardLayout from '@/components/layout/DashboardLayout';
import SearchBar from '@/components/controls/SearchBar';
import { useCompanyIdentity } from '@/hooks/useCompanyIdentity';
import { ComparisonResponse, PeerSnapshot, getPeerComparison } from '@/services/compare';
import { findSimilarCompanies } from '@/services/memory';

const MAX_MEMORY_PEERS = 10;
const MAX_COMPARISON_PEERS = 12;

function dedupeTickers(tickers: string[]): string[] {
    const seen = new Set<string>();
    const output: string[] = [];

    for (const raw of tickers) {
        const ticker = raw.trim().toUpperCase();
        if (!ticker || seen.has(ticker)) continue;
        seen.add(ticker);
        output.push(ticker);
    }

    return output;
}

function titleize(value?: string | null): string {
    if (!value) return 'Unknown';
    return value
        .replace(/_/g, ' ')
        .split(' ')
        .filter(Boolean)
        .map((part) => part[0].toUpperCase() + part.slice(1))
        .join(' ');
}

function statusBadgeClass(value?: string | null): string {
    const normalized = (value ?? '').toLowerCase();

    if (
        normalized.includes('undervalued') ||
        normalized.includes('above_average') ||
        normalized.includes('safest') ||
        normalized.includes('strong')
    ) {
        return 'badge badge-green';
    }
    if (
        normalized.includes('overvalued') ||
        normalized.includes('below_average') ||
        normalized.includes('highest_risk') ||
        normalized.includes('weak')
    ) {
        return 'badge badge-red';
    }
    if (normalized.includes('fairly') || normalized.includes('in_line') || normalized.includes('average')) {
        return 'badge badge-yellow';
    }
    return 'badge badge-blue';
}

function formatMultiple(value?: number | null): string {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(2)}x`;
}

function formatPercent(value?: number | null): string {
    if (value === undefined || value === null) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
}

function formatScore(value?: number | null): string {
    if (value === undefined || value === null) return 'N/A';
    return value.toFixed(1);
}

function MetricRow({
    label,
    status,
    target,
    peer,
}: {
    label: string;
    status?: string | null;
    target: string;
    peer: string;
}) {
    return (
        <div className="rounded-xl p-3 border" style={{ borderColor: 'var(--border)', background: 'rgba(17,24,39,0.55)' }}>
            <div className="flex items-center justify-between gap-2 mb-2">
                <p className="text-xs font-semibold text-white">{label}</p>
                {status && <span className={statusBadgeClass(status)}>{titleize(status)}</span>}
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                    <p style={{ color: 'var(--text-muted)' }}>Target</p>
                    <p className="text-sm font-semibold text-white">{target}</p>
                </div>
                <div>
                    <p style={{ color: 'var(--text-muted)' }}>Peer Avg</p>
                    <p className="text-sm font-semibold text-white">{peer}</p>
                </div>
            </div>
        </div>
    );
}

function PeerCard({ peer, fromMemory }: { peer: PeerSnapshot; fromMemory: boolean }) {
    return (
        <div className="rounded-xl p-3 border" style={{ borderColor: 'var(--border)', background: 'rgba(17,24,39,0.7)' }}>
            <div className="flex items-center justify-between gap-2">
                <p className="font-semibold text-white">{peer.ticker}</p>
                <div className="flex items-center gap-2">
                    {fromMemory && <span className="badge badge-blue">Memory</span>}
                    <span className={statusBadgeClass(peer.financial_health_classification)}>
                        {titleize(peer.financial_health_classification)}
                    </span>
                </div>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3 text-xs" style={{ color: 'var(--text-muted)' }}>
                <p>Risk: <span className="text-white">{formatScore(peer.composite_risk_score)}</span></p>
                <p>Health: <span className="text-white">{formatScore(peer.financial_health_score)}</span></p>
                <p>ROE: <span className="text-white">{formatPercent(peer.roe)}</span></p>
                <p>Margin: <span className="text-white">{formatPercent(peer.net_profit_margin)}</span></p>
            </div>
            <div className="grid grid-cols-2 gap-2 mt-3">
                <Link
                    href={`/quick?ticker=${encodeURIComponent(peer.ticker)}`}
                    className="text-center px-3 py-2 rounded-lg text-xs font-semibold transition-colors"
                    style={{ background: 'rgba(59,130,246,0.15)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.35)' }}
                >
                    Quick
                </Link>
                <Link
                    href={`/deep?ticker=${encodeURIComponent(peer.ticker)}`}
                    className="text-center px-3 py-2 rounded-lg text-xs font-semibold transition-colors"
                    style={{ background: 'rgba(16,185,129,0.15)', color: '#86efac', border: '1px solid rgba(16,185,129,0.35)' }}
                >
                    Deep
                </Link>
            </div>
        </div>
    );
}

function CompareContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState((params.get('ticker') ?? '').toUpperCase());
    const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [memoryCandidates, setMemoryCandidates] = useState<string[]>([]);
    const [memoryApplied, setMemoryApplied] = useState<string[]>([]);
    const [memoryNote, setMemoryNote] = useState('');
    const activeTicker = (comparison?.ticker ?? ticker ?? '').toUpperCase();
    const { displayLabel } = useCompanyIdentity(activeTicker);

    const analyze = async (inputTicker: string) => {
        const normalizedTicker = inputTicker.trim().toUpperCase();
        if (!normalizedTicker) return;

        setTicker(normalizedTicker);
        setError('');
        setLoading(true);

        try {
            const [baseComparison, memoryResponse] = await Promise.all([
                getPeerComparison(normalizedTicker),
                findSimilarCompanies(normalizedTicker, MAX_MEMORY_PEERS).catch(() => null),
            ]);

            const memoryPeers = dedupeTickers(
                (memoryResponse?.similar_results ?? [])
                    .map((item) => item.ticker)
                    .filter((peer) => peer.toUpperCase() !== normalizedTicker)
            );

            const mergedPeers = dedupeTickers([...baseComparison.peers, ...memoryPeers]).slice(0, MAX_COMPARISON_PEERS);

            const finalComparison =
                mergedPeers.length > baseComparison.peers.length
                    ? await getPeerComparison(normalizedTicker, mergedPeers)
                    : baseComparison;

            const appliedFromMemory = finalComparison.peers.filter((peer) => memoryPeers.includes(peer));

            setComparison(finalComparison);
            setMemoryCandidates(memoryPeers);
            setMemoryApplied(appliedFromMemory);

            if (memoryResponse === null) {
                setMemoryNote('Memory similarity service is unavailable. Showing sector peers only.');
            } else if (memoryPeers.length === 0) {
                setMemoryNote('No memory-based peers found for this ticker.');
            } else if (appliedFromMemory.length > 0) {
                setMemoryNote(
                    `Memory-enriched peer set applied: ${appliedFromMemory.join(', ')}.`
                );
            } else {
                setMemoryNote('Memory peers were found, but only peers with full market data are shown.');
            }
        } catch {
            setError('Comparison analysis failed.');
            setComparison(null);
            setMemoryCandidates([]);
            setMemoryApplied([]);
            setMemoryNote('');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const queryTicker = params.get('ticker');
        if (queryTicker) analyze(queryTicker);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const memoryAppliedSet = useMemo(() => new Set(memoryApplied), [memoryApplied]);

    const universeSize =
        comparison?.comparison_universe_size ??
        ((comparison?.peers?.length ?? 0) > 0 ? (comparison?.peers?.length ?? 0) + 1 : 0);
    const riskUniverse = comparison?.risk_comparison?.universe_size ?? universeSize;

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(16,185,129,0.2)' }}>
                    <GitCompare size={16} style={{ color: '#10b981' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Peer Comparison</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        Memory-enriched benchmarking across valuation, quality, growth, and risk
                    </p>
                    {activeTicker && (
                        <p className="text-xs mt-1" style={{ color: '#86efac' }}>
                            {displayLabel}
                        </p>
                    )}
                </div>
            </div>

            <SearchBar onAnalyze={analyze} loading={loading} defaultValue={ticker} />

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
                        <div className="skeleton h-36 rounded-xl" />
                        <div className="skeleton h-36 rounded-xl" />
                    </div>
                </div>
            )}

            {comparison && !loading && (
                <div className="space-y-4">
                    <div
                        className="card"
                        style={{
                            borderColor: 'rgba(16,185,129,0.35)',
                            background: 'linear-gradient(130deg, rgba(16,185,129,0.16), rgba(17,24,39,0.95) 40%)',
                        }}
                    >
                        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                            <div>
                                <p className="text-xs uppercase tracking-wide text-emerald-300">Strategic Summary</p>
                                <h2 className="text-lg font-semibold text-white mt-1">
                                    {comparison.ticker} vs {comparison.peers.length} peers
                                </h2>
                                <p className="text-sm mt-2 leading-relaxed" style={{ color: 'var(--text-primary)' }}>
                                    {comparison.strategic_summary ?? 'No strategic summary available.'}
                                </p>
                            </div>
                            <span className={statusBadgeClass(comparison.financial_health_position)}>
                                {titleize(comparison.financial_health_position)}
                            </span>
                        </div>

                        <p className="text-xs mt-4" style={{ color: 'var(--text-muted)' }}>
                            Peers: {comparison.peers.join(', ') || 'N/A'}
                        </p>
                        {!!memoryNote && (
                            <p className="text-xs mt-1" style={{ color: '#7dd3fc' }}>
                                {memoryNote}
                            </p>
                        )}
                        {memoryCandidates.length > 0 && (
                            <p className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                                Memory suggestions considered: {memoryCandidates.join(', ')}
                            </p>
                        )}
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div className="card p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <Users size={14} style={{ color: '#60a5fa' }} />
                                <p className="text-xs font-semibold text-white">Universe Size</p>
                            </div>
                            <p className="text-lg font-bold text-white">{universeSize || 'N/A'}</p>
                        </div>
                        <div className="card p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <Target size={14} style={{ color: '#34d399' }} />
                                <p className="text-xs font-semibold text-white">ROE Rank</p>
                            </div>
                            <p className="text-lg font-bold text-white">
                                #{comparison.profitability_comparison.roe_rank}/{riskUniverse || 'N/A'}
                            </p>
                        </div>
                        <div className="card p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <Shield size={14} style={{ color: '#fbbf24' }} />
                                <p className="text-xs font-semibold text-white">Risk Rank</p>
                            </div>
                            <p className="text-lg font-bold text-white">
                                #{comparison.risk_comparison.relative_risk_rank}/{riskUniverse || 'N/A'}
                            </p>
                        </div>
                        <div className="card p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <BarChart3 size={14} style={{ color: '#a78bfa' }} />
                                <p className="text-xs font-semibold text-white">Safety</p>
                            </div>
                            <span className={statusBadgeClass(comparison.risk_comparison.safety_position)}>
                                {titleize(comparison.risk_comparison.safety_position)}
                            </span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                        <div className="card space-y-3">
                            <h3 className="text-sm font-semibold text-white">Valuation Lens</h3>
                            <MetricRow
                                label="P/E"
                                status={comparison.valuation_comparison.pe_status}
                                target={formatMultiple(comparison.valuation_comparison.target_pe)}
                                peer={formatMultiple(comparison.valuation_comparison.peer_avg_pe)}
                            />
                            <MetricRow
                                label="P/B"
                                status={comparison.valuation_comparison.pb_status}
                                target={formatMultiple(comparison.valuation_comparison.target_pb)}
                                peer={formatMultiple(comparison.valuation_comparison.peer_avg_pb)}
                            />
                            <MetricRow
                                label="EV/EBITDA"
                                status={comparison.valuation_comparison.ev_ebitda_status}
                                target={formatMultiple(comparison.valuation_comparison.target_ev_ebitda)}
                                peer={formatMultiple(comparison.valuation_comparison.peer_avg_ev_ebitda)}
                            />
                        </div>

                        <div className="card space-y-3">
                            <h3 className="text-sm font-semibold text-white">Operating and Growth</h3>
                            <MetricRow
                                label="Net Margin"
                                status={comparison.profitability_comparison.margin_position}
                                target={formatPercent(comparison.profitability_comparison.target_net_margin)}
                                peer={formatPercent(comparison.profitability_comparison.peer_avg_net_margin)}
                            />
                            <MetricRow
                                label="ROE"
                                target={formatPercent(comparison.profitability_comparison.target_roe)}
                                peer={formatPercent(comparison.profitability_comparison.peer_avg_roe)}
                            />
                            <MetricRow
                                label="Revenue Growth"
                                status={comparison.growth_comparison.revenue_growth_position}
                                target={formatPercent(comparison.growth_comparison.target_revenue_growth)}
                                peer={formatPercent(comparison.growth_comparison.peer_avg_revenue_growth)}
                            />
                            <MetricRow
                                label="Earnings Growth"
                                status={comparison.growth_comparison.earnings_growth_position}
                                target={formatPercent(comparison.growth_comparison.target_earnings_growth)}
                                peer={formatPercent(comparison.growth_comparison.peer_avg_earnings_growth)}
                            />
                        </div>
                    </div>

                    <div className="card">
                        <h3 className="text-sm font-semibold text-white mb-3">Peer Matrix</h3>
                        {(comparison.peer_snapshots ?? []).length > 0 ? (
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
                                {(comparison.peer_snapshots ?? []).map((peer) => (
                                    <PeerCard key={peer.ticker} peer={peer} fromMemory={memoryAppliedSet.has(peer.ticker)} />
                                ))}
                            </div>
                        ) : (
                            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>
                                Peer snapshots are not available for this run.
                            </p>
                        )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Strengths</h3>
                            <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                {(comparison.strengths ?? []).slice(0, 5).map((item, idx) => (
                                    <p key={idx}>- {item}</p>
                                ))}
                            </div>
                        </div>
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-3">Weaknesses</h3>
                            <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
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
