'use client';
import { useState } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { searchMemory } from '@/services/memory';
import { Database, Search, TrendingUp, AlertTriangle, Loader2 } from 'lucide-react';

export default function MemoryPage() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<{
        similar_results: { ticker: string; similarity_score: number; summary_excerpt: string; risk_score: number; insight_type: string }[];
        total_found: number;
    } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const search = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;
        setLoading(true);
        setError('');
        try {
            const res = await searchMemory(query, 5);
            setResults(res);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string | { detail?: string } } } };
            const detail = err?.response?.data?.detail;
            const message = typeof detail === 'object' ? detail?.detail : detail;
            setError(message ?? 'Memory search failed. Make sure Qdrant is connected and run at least one deep analysis first.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="max-w-3xl mx-auto space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(168,85,247,0.2)' }}>
                        <Database size={16} style={{ color: '#a855f7' }} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Memory Search</h1>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Semantic search through your past research sessions</p>
                    </div>
                </div>

                <form onSubmit={search} className="flex gap-2">
                    <div className="relative flex-1">
                        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
                        <input value={query} onChange={(e) => setQuery(e.target.value)}
                            placeholder='e.g. "tech companies with high growth" or "similar to AAPL"'
                            className="w-full pl-9 pr-3 py-3 rounded-xl text-sm text-white outline-none"
                            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                        />
                    </div>
                    <button type="submit" disabled={loading || !query.trim()}
                        className="px-5 py-3 rounded-xl text-sm font-semibold text-white disabled:opacity-50 flex items-center gap-2"
                        style={{ background: 'var(--accent)' }}>
                        {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                        Search
                    </button>
                </form>

                {error && (
                    <div className="flex items-center gap-2 p-4 rounded-xl text-sm" style={{ background: 'rgba(239,68,68,0.1)', color: '#ef4444' }}>
                        <AlertTriangle size={14} /> {error}
                    </div>
                )}

                {results && (
                    <div className="space-y-3">
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Found {results.total_found} similar result{results.total_found !== 1 ? 's' : ''}
                        </p>
                        {results.total_found === 0 && (
                            <div className="card text-xs" style={{ color: 'var(--text-muted)' }}>
                                No stored memory matches yet. Run a Deep Analysis first, then search again.
                            </div>
                        )}
                        {results.similar_results.map((r, i) => (
                            <div key={i} className="card hover:border-blue-500/30 transition-all">
                                <div className="flex items-start justify-between mb-2">
                                    <div>
                                        <span className="text-base font-bold text-white">{r.ticker}</span>
                                        <span className="ml-2 badge badge-blue">{r.insight_type}</span>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Similarity</p>
                                        <p className="text-sm font-bold" style={{ color: '#3b82f6' }}>
                                            {(r.similarity_score * 100).toFixed(1)}%
                                        </p>
                                    </div>
                                </div>
                                <p className="text-xs leading-relaxed mb-2" style={{ color: 'var(--text-muted)' }}>{r.summary_excerpt}</p>
                                <div className="flex items-center gap-1.5">
                                    <TrendingUp size={11} style={{ color: 'var(--text-muted)' }} />
                                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>Risk Score: </span>
                                    <span className="text-xs font-medium" style={{ color: r.risk_score > 60 ? '#ef4444' : '#10b981' }}>
                                        {r.risk_score.toFixed(0)}/100
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
