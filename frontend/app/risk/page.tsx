'use client';
import { Suspense, useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { ShieldAlert } from 'lucide-react';
import SearchBar from '@/components/controls/SearchBar';
import RiskPanel from '@/components/panels/RiskPanel';
import { getRiskProfile, RiskResponse } from '@/services/risk';

function RiskContent() {
    const params = useSearchParams();
    const [ticker, setTicker] = useState(params.get('ticker') ?? '');
    const [risk, setRisk] = useState<RiskResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const analyze = async (inputTicker: string) => {
        setTicker(inputTicker);
        setLoading(true);
        setError('');
        try {
            const res = await getRiskProfile(inputTicker);
            setRisk(res);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string | { detail?: string } } } };
            const detail = err?.response?.data?.detail;
            setError(typeof detail === 'object' ? detail?.detail ?? 'Risk analysis failed.' : detail ?? 'Risk analysis failed.');
            setRisk(null);
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

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(239,68,68,0.2)' }}>
                    <ShieldAlert size={16} style={{ color: '#ef4444' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Risk Overview</h1>
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Full risk profile including leverage, liquidity, earnings, and hidden risks</p>
                </div>
            </div>

            <SearchBar onAnalyze={analyze} loading={loading} defaultValue={ticker} />

            {error && (
                <div className="card text-sm" style={{ color: '#ef4444' }}>
                    {error}
                </div>
            )}

            {(loading || risk) && (
                <RiskPanel data={(risk as Parameters<typeof RiskPanel>[0]['data'])} loading={loading} />
            )}
        </div>
    );
}

export default function RiskPage() {
    return (
        <DashboardLayout>
            <Suspense fallback={<div className="max-w-3xl mx-auto skeleton h-40 rounded-xl" />}>
                <RiskContent />
            </Suspense>
        </DashboardLayout>
    );
}
