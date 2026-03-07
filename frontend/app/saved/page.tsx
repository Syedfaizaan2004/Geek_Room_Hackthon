'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { BookOpen, Clock3, Database, Search } from 'lucide-react';

import DashboardLayout from '@/components/layout/DashboardLayout';
import { MemoryRecentResult, getRecentMemory } from '@/services/memory';

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

export default function SavedPage() {
    const [items, setItems] = useState<MemoryRecentResult[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        let active = true;

        getRecentMemory(24)
            .then((res) => {
                if (!active) return;
                setItems(res);
            })
            .catch(() => {
                if (!active) return;
                setError('Could not load saved analyses. Memory service may be unavailable.');
                setItems([]);
            })
            .finally(() => {
                if (!active) return;
                setLoading(false);
            });

        return () => {
            active = false;
        };
    }, []);

    const uniqueTickers = useMemo(() => new Set(items.map((item) => item.ticker)).size, [items]);
    const avgRisk = useMemo(() => {
        if (items.length === 0) return null;
        return items.reduce((sum, item) => sum + (item.risk_score ?? 0), 0) / items.length;
    }, [items]);
    const avgHealth = useMemo(() => {
        if (items.length === 0) return null;
        return items.reduce((sum, item) => sum + (item.financial_health_score ?? 0), 0) / items.length;
    }, [items]);

    return (
        <DashboardLayout>
            <div className="max-w-5xl mx-auto space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.2)' }}>
                        <BookOpen size={16} style={{ color: '#6366f1' }} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Saved Analyses</h1>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Your recent stored insights from semantic memory
                        </p>
                    </div>
                </div>

                {loading && (
                    <div className="space-y-3">
                        <div className="skeleton h-32 rounded-xl" />
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            <div className="skeleton h-28 rounded-xl" />
                            <div className="skeleton h-28 rounded-xl" />
                        </div>
                    </div>
                )}

                {!loading && (
                    <>
                        <div
                            className="card"
                            style={{
                                borderColor: 'rgba(99,102,241,0.4)',
                                background: 'linear-gradient(130deg, rgba(99,102,241,0.16), rgba(17,24,39,0.95) 45%)',
                            }}
                        >
                            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
                                <div>
                                    <p className="text-xs uppercase tracking-wide" style={{ color: '#c4b5fd' }}>
                                        Memory Portfolio
                                    </p>
                                    <p className="text-sm mt-1" style={{ color: 'var(--text-primary)' }}>
                                        Track what you analyzed recently and jump back into research quickly.
                                    </p>
                                </div>
                                <Link
                                    href="/memory"
                                    className="inline-flex items-center gap-1 px-3 py-2 rounded-lg text-xs font-semibold"
                                    style={{ background: 'rgba(59,130,246,0.18)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.35)' }}
                                >
                                    <Search size={12} />
                                    Open Memory Search
                                </Link>
                            </div>

                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
                                <Stat label="Saved Analyses" value={items.length.toString()} />
                                <Stat label="Unique Tickers" value={uniqueTickers.toString()} />
                                <Stat label="Avg Risk" value={avgRisk == null ? 'N/A' : avgRisk.toFixed(1)} color={avgRisk == null ? undefined : scoreColor(avgRisk, true)} />
                                <Stat label="Avg Health" value={avgHealth == null ? 'N/A' : avgHealth.toFixed(1)} color={avgHealth == null ? undefined : scoreColor(avgHealth)} />
                            </div>
                        </div>

                        {error && (
                            <div className="card text-sm" style={{ color: '#ef4444' }}>
                                {error}
                            </div>
                        )}

                        {items.length === 0 ? (
                            <div className="card text-center py-12">
                                <Database size={30} className="mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
                                <p className="text-sm text-white mb-1">No saved analyses yet</p>
                                <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>
                                    Run Quick or Deep analysis to populate memory, then come back here.
                                </p>
                                <div className="flex items-center justify-center gap-2">
                                    <Link href="/quick" className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ background: 'rgba(59,130,246,0.85)' }}>
                                        Quick Analysis
                                    </Link>
                                    <Link href="/deep" className="px-4 py-2 rounded-lg text-sm font-medium text-white" style={{ background: 'rgba(16,185,129,0.8)' }}>
                                        Deep Research
                                    </Link>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {items.map((item, index) => (
                                    <div
                                        key={`${item.ticker}-${item.stored_at ?? index}-${index}`}
                                        className="card"
                                        style={{ background: 'rgba(17,24,39,0.86)' }}
                                    >
                                        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-3">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-base font-bold text-white">{item.ticker}</span>
                                                    <span className="badge badge-blue">{item.insight_type}</span>
                                                </div>
                                                <div className="flex items-center gap-1 mt-1 text-xs" style={{ color: 'var(--text-muted)' }}>
                                                    <Clock3 size={11} />
                                                    {formatDateTime(item.stored_at)}
                                                </div>
                                            </div>
                                            <div className="grid grid-cols-2 gap-2 text-xs">
                                                <span className="px-2 py-1 rounded-md" style={{ background: 'rgba(255,255,255,0.05)' }}>
                                                    Risk: <span style={{ color: scoreColor(item.risk_score ?? 0, true) }}>{(item.risk_score ?? 0).toFixed(0)}</span>
                                                </span>
                                                <span className="px-2 py-1 rounded-md" style={{ background: 'rgba(255,255,255,0.05)' }}>
                                                    Health: <span style={{ color: scoreColor(item.financial_health_score ?? 0) }}>{(item.financial_health_score ?? 0).toFixed(0)}</span>
                                                </span>
                                            </div>
                                        </div>

                                        <p className="text-xs leading-relaxed mt-3" style={{ color: 'var(--text-muted)' }}>
                                            {item.summary_excerpt || 'No summary excerpt available.'}
                                        </p>

                                        <div className="grid grid-cols-3 gap-2 mt-3">
                                            <Link
                                                href={`/quick?ticker=${encodeURIComponent(item.ticker)}`}
                                                className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                                style={{ background: 'rgba(59,130,246,0.15)', color: '#93c5fd', border: '1px solid rgba(59,130,246,0.35)' }}
                                            >
                                                Quick
                                            </Link>
                                            <Link
                                                href={`/deep?ticker=${encodeURIComponent(item.ticker)}`}
                                                className="text-center px-3 py-2 rounded-lg text-xs font-semibold"
                                                style={{ background: 'rgba(16,185,129,0.15)', color: '#86efac', border: '1px solid rgba(16,185,129,0.35)' }}
                                            >
                                                Deep
                                            </Link>
                                            <Link
                                                href={`/compare?ticker=${encodeURIComponent(item.ticker)}`}
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
                    </>
                )}
            </div>
        </DashboardLayout>
    );
}

function Stat({ label, value, color }: { label: string; value: string; color?: string }) {
    return (
        <div className="rounded-lg p-3" style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)' }}>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>{label}</p>
            <p className="text-sm font-semibold mt-1" style={{ color: color ?? 'white' }}>{value}</p>
        </div>
    );
}
