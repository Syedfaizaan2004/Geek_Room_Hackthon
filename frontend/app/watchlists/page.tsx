'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { Star, Search } from 'lucide-react';
import { getRecommendations, RecommendationResponse } from '@/services/recommendations';

function RecommendationsContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState((params.get('ticker') ?? '').toUpperCase());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [data, setData] = useState<RecommendationResponse | null>(null);

    const run = async (inputTicker: string) => {
        const t = inputTicker.trim().toUpperCase();
        if (!t) return;
        setTicker(t);
        setLoading(true);
        setError('');
        try {
            const res = await getRecommendations(t);
            setData(res);
        } catch {
            setError('Failed to fetch recommendations for this ticker.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const t = params.get('ticker');
        if (t) {
            run(t);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(251,191,36,0.2)' }}>
                    <Star size={16} style={{ color: '#fbbf24' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Recommendations Hub</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Personalized next actions and similar companies</p>
                </div>
            </div>

            <div className="flex gap-2">
                <input
                    value={ticker}
                    onChange={(e) => setTicker(e.target.value.toUpperCase())}
                    placeholder="Enter ticker (e.g. MSFT)"
                    maxLength={10}
                    className="flex-1 px-3 py-3 rounded-xl text-sm text-white outline-none"
                    style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                />
                <button
                    onClick={() => run(ticker)}
                    disabled={loading || !ticker.trim()}
                    className="px-4 py-3 rounded-xl text-sm font-semibold text-white flex items-center gap-2 disabled:opacity-50"
                    style={{ background: 'var(--accent)' }}
                >
                    <Search size={14} />
                    Analyze
                </button>
            </div>

            {error && (
                <div className="card text-sm" style={{ color: '#ef4444' }}>
                    {error}
                </div>
            )}

            {loading && <div className="skeleton h-36 rounded-xl" />}

            {data && !loading && (
                <div className="space-y-4">
                    <div className="card">
                        <h3 className="text-sm font-semibold text-white mb-2">Next Actions</h3>
                        <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                            {(data.next_actions ?? []).map((a, idx) => (
                                <p key={idx}>
                                    <span className="text-white">{a.action_type.replace(/_/g, ' ')}:</span> {a.explanation}
                                </p>
                            ))}
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-2">Similar Companies</h3>
                            <div className="space-y-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                                {(data.similar_companies ?? []).map((c, idx) => (
                                    <p key={idx}>
                                        <span className="text-white">{c.ticker}</span> ({(c.similarity_score * 100).toFixed(1)}%) - {c.reason}
                                    </p>
                                ))}
                                {(data.similar_companies ?? []).length === 0 && <p>No similar companies found.</p>}
                            </div>
                        </div>

                        <div className="card">
                            <h3 className="text-sm font-semibold text-white mb-2">Memory Reminders</h3>
                            <div className="space-y-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                                {(data.memory_reminders ?? []).map((r, idx) => <p key={idx}>- {r}</p>)}
                                {(data.memory_reminders ?? []).length === 0 && <p>No reminders available.</p>}
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
