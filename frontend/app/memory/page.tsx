'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { AlertTriangle, Clock3, Database, Loader2, Search, TrendingUp } from 'lucide-react';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { MemorySearchResponse, searchMemory } from '@/services/memory';

const SAMPLE_QUERIES = [
    'tech companies with high growth',
    'companies like AAPL',
    'strong cashflow and low risk',
    'recent bearish analyses',
];

function formatDateTime(ts?: string | null): string {
    if (!ts) return 'Unknown';
    const date = new Date(ts);
    if (Number.isNaN(date.getTime())) return 'Unknown';
    return date.toLocaleString();
}

function scoreColor(score: number, inverse = false): string {
    if (inverse) {
        if (score >= 70) return '#ef4444';
        if (score >= 45) return '#f59e0b';
        return '#10b981';
    }
    if (score >= 70) return '#10b981';
    if (score >= 45) return '#f59e0b';
    return '#ef4444';
}

export default function MemoryPage() {
    const [query, setQuery] = useState('');
    const [topK, setTopK] = useState(8);
    const [results, setResults] = useState<MemorySearchResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const runSearch = async (incomingQuery?: string) => {
        const searchQuery = (incomingQuery ?? query).trim();
        if (!searchQuery) return;

        setLoading(true);
        setError('');

        try {
            const response = await searchMemory(searchQuery, topK);
            setQuery(searchQuery);
            setResults(response);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string | { detail?: string } } } };
            const detail = err?.response?.data?.detail;
            const message = typeof detail === 'object' ? detail?.detail : detail;
            setError(message ?? 'Memory search failed. Ensure Qdrant is connected and run at least one analysis first.');
            setResults(null);
        } finally {
            setLoading(false);
        }
    };

    const summary = useMemo(() => {
        if (!results || results.total_found === 0) return null;
        const avgRisk =
            results.similar_results.reduce((sum, row) => sum + (row.risk_score ?? 0), 0) / results.similar_results.length;
        const avgHealth =
            results.similar_results.reduce((sum, row) => sum + (row.financial_health_score ?? 0), 0) / results.similar_results.length;
        return {
            avgRisk,
            avgHealth,
        };
    }, [results]);

    return (
        <DashboardLayout>
            <div className="max-w-5xl mx-auto space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(168,85,247,0.2)' }}>
                        <Database size={16} style={{ color: '#a855f7' }} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Memory Search</h1>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Semantic recall across your past research sessions
                        </p>
                    </div>
                </div>

                <div className="card space-y-3">
                    <form
                        onSubmit={(e) => {
                            e.preventDefault();
                            runSearch();
                        }}
                        className="flex flex-col md:flex-row gap-2"
                    >
                        <div className="relative flex-1">
                            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
                            <input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder='e.g. "tech companies with high growth" or "similar to AAPL"'
                                className="w-full pl-9 pr-3 py-3 rounded-xl text-sm text-white outline-none"
                                style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}
                            />
                        </div>

                        <select
                            value={topK}
                            onChange={(e) => setTopK(Number(e.target.value))}
                            className="px-3 py-3 rounded-xl text-sm text-white outline-none"
                            style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}
                        >
                            <option value={5}>Top 5</option>
                            <option value={8}>Top 8</option>
                            <option value={12}>Top 12</option>
                            <option value={20}>Top 20</option>
                        </select>

                        <button
                            type="submit"
                            disabled={loading || !query.trim()}
                            className="px-5 py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-50 flex items-center justify-center gap-2"
                            style={{ background: 'var(--accent)' }}
                        >
                            {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                            Search
                        </button>
                    </form>

                    <div className="flex flex-wrap gap-2">
                        {SAMPLE_QUERIES.map((sample) => (
                            <button
                                key={sample}
                                type="button"
                                onClick={() => runSearch(sample)}
                                className="px-3 py-1.5 rounded-lg text-xs transition-colors"
                                style={{ background: 'rgba(255,255,255,0.03)', color: 'var(--text-muted)', border: '1px solid var(--border)' }}
                            >
                                {sample}
                            </button>
                        ))}
                    </div>
                </div>

                {error && (
                    <div className="flex items-center gap-2 p-4 rounded-xl text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                        <AlertTriangle size={14} /> {error}
                    </div>
                )}

                {loading && (
                    <div className="space-y-3">
                        <div className="skeleton h-20 rounded-xl" />
                        <div className="skeleton h-28 rounded-xl" />
                        <div className="skeleton h-28 rounded-xl" />
                    </div>
                )}

                {results && !loading && (
                    <div className="space-y-4">
                        <div
                            className="card"
                            style={{
                                borderColor: 'rgba(168,85,247,0.35)',
                                background: 'linear-gradient(130deg, rgba(168,85,247,0.16), rgba(17,24,39,0.95) 42%)',
                            }}
                        >
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                                <div>
                                    <p className="text-xs uppercase tracking-wide" style={{ color: '#d8b4fe' }}>
                                        Query Insights
                                    </p>
                                    <p className="text-sm text-white mt-1">&quot;{results.query}&quot;</p>
                                </div>
                                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                    Found {results.total_found} result{results.total_found !== 1 ? 's' : ''}
                                </div>
                            </div>
                            {summary && (
                                <div className="grid grid-cols-2 gap-3 mt-4">
                                    <Stat label="Avg Risk" value={summary.avgRisk.toFixed(1)} color={scoreColor(summary.avgRisk, true)} />
                                    <Stat label="Avg Health" value={summary.avgHealth.toFixed(1)} color={scoreColor(summary.avgHealth)} />
                                </div>
                            )}
                        </div>

                        {results.total_found === 0 && (
                            <div className="card text-xs" style={{ color: 'var(--text-muted)' }}>
                                No stored memory matches yet. Run a Deep Analysis first, then search again.
                            </div>
                        )}

                        {results.similar_results.map((row, index) => (
                            <div key={`${row.ticker}-${index}-${row.stored_at ?? ''}`} className="card" style={{ background: 'rgba(17,24,39,0.86)' }}>
                                <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                                    <div>
                                        <div className="flex items-center gap-2">
                                            <span className="text-base font-bold text-white">{row.ticker}</span>
                                            <span className="badge badge-blue">{row.insight_type}</span>
                                        </div>
                                        <div className="flex items-center gap-1 mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                                            <Clock3 size={11} />
                                            {formatDateTime(row.stored_at)}
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Similarity</p>
                                        <p className="text-sm font-bold" style={{ color: '#3b82f6' }}>
                                            {(row.similarity_score * 100).toFixed(1)}%
                                        </p>
                                    </div>
                                </div>

                                <div className="mt-2 h-2 rounded-full overflow-hidden" style={{ background: 'rgba(255,255,255,0.08)' }}>
                                    <div
                                        className="h-full"
                                        style={{
                                            width: `${Math.max(0, Math.min(100, row.similarity_score * 100)).toFixed(1)}%`,
                                            background: 'linear-gradient(90deg, #3b82f6, #60a5fa)',
                                        }}
                                    />
                                </div>

                                <p className="text-xs leading-relaxed mt-3" style={{ color: 'var(--text-muted)' }}>
                                    {row.summary_excerpt}
                                </p>

                                <div className="grid grid-cols-2 gap-2 mt-3 text-xs">
                                    <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Risk Score: </span>
                                        <span style={{ color: scoreColor(row.risk_score ?? 0, true), fontWeight: 700 }}>
                                            {(row.risk_score ?? 0).toFixed(0)}/100
                                        </span>
                                    </div>
                                    <div className="rounded-lg p-2" style={{ background: 'rgba(255,255,255,0.04)' }}>
                                        <span style={{ color: 'var(--text-muted)' }}>Health Score: </span>
                                        <span style={{ color: scoreColor(row.financial_health_score ?? 0), fontWeight: 700 }}>
                                            {(row.financial_health_score ?? 0).toFixed(0)}/100
                                        </span>
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-2 mt-3">
                                    <Link
                                        href={`/quick?ticker=${encodeURIComponent(row.ticker)}`}
                                        className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                        style={{ background: 'rgba(59,130,246,0.15)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.35)' }}
                                    >
                                        Quick
                                    </Link>
                                    <Link
                                        href={`/deep?ticker=${encodeURIComponent(row.ticker)}`}
                                        className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                        style={{ background: 'rgba(16,185,129,0.15)', color: '#86efac', border: '1px solid rgba(16,185,129,0.35)' }}
                                    >
                                        Deep
                                    </Link>
                                    <Link
                                        href={`/compare?ticker=${encodeURIComponent(row.ticker)}`}
                                        className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                        style={{ background: 'rgba(168,85,247,0.15)', color: '#d8b4fe', border: '1px solid rgba(168,85,247,0.35)' }}
                                    >
                                        Compare
                                    </Link>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
    return (
        <div className="rounded-lg p-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</p>
            <p className="text-sm font-semibold mt-1" style={{ color: color ?? 'white' }}>
                <TrendingUp size={12} className="inline mr-1" />
                {value}
            </p>
        </div>
    );
}
