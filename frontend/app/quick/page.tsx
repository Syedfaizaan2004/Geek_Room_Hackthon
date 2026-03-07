'use client';
import { Suspense } from 'react';
import { useState, useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import SearchBar from '@/components/controls/SearchBar';
import ModeToggle, { AnalysisMode } from '@/components/controls/ModeToggle';
import CompanySnapshot from '@/components/panels/CompanySnapshot';
import RiskPanel from '@/components/panels/RiskPanel';
import ConfidencePanel from '@/components/panels/ConfidencePanel';
import InsightsPanel from '@/components/panels/InsightsPanel';
// Phase 17 components
import ExecutiveSummaryBanner from '@/components/ui/ExecutiveSummaryBanner';
import SmartRecommendationPanel from '@/components/ui/SmartRecommendationPanel';
import MemoryHighlightBanner from '@/components/ui/MemoryHighlightBanner';
import TransparencyPanel from '@/components/ui/TransparencyPanel';
import DataFreshnessBar from '@/components/ui/DataFreshnessBar';
import ExportBar from '@/components/ui/ExportBar';
import { runAnalysis, AgentResponseData } from '@/services/agent';
import { useCompanyIdentity } from '@/hooks/useCompanyIdentity';
import { AlertTriangle, Zap, RefreshCw } from 'lucide-react';

function QuickContent() {
    const router = useRouter();
    const params = useSearchParams();
    const [ticker, setTicker] = useState(params.get('ticker') ?? '');
    const [mode, setMode] = useState<AnalysisMode>('quick');
    const [data, setData] = useState<AgentResponseData | null>(null);
    const [response, setResponse] = useState<import('@/services/agent').AgentResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const resultRef = useRef<HTMLDivElement>(null);

    const analyze = async (t: string) => {
        setTicker(t);
        setError('');
        setLoading(true);
        try {
            const res = await runAnalysis(t, 'quick');
            setData(res.data);
            setResponse(res);
            setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } } };
            setError(err?.response?.data?.detail ?? 'Analysis failed. Check ticker and try again.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const t = params.get('ticker');
        if (t) analyze(t);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const d = data;
    const recs = d?.recommendations as Parameters<typeof SmartRecommendationPanel>[0]['recommendations'];
    const demoMode = !!(d?.demo_mode);
    const activeTicker = (response?.ticker ?? ticker ?? '').toUpperCase();
    const { displayLabel } = useCompanyIdentity(activeTicker);

    return (
        <div className="max-w-5xl mx-auto space-y-5">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(59,130,246,0.2)' }}>
                    <Zap size={16} style={{ color: '#3b82f6' }} />
                </div>
                <div>
                    <h1 className="text-xl font-bold text-white">Quick Analysis</h1>
                    {activeTicker && (
                        <p className="text-xs mt-1" style={{ color: '#93c5fd' }}>
                            {displayLabel}
                        </p>
                    )}
                    <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Fast 4-engine snapshot — market · risk · confidence · insights</p>
                </div>
            </div>

            <ModeToggle mode={mode} onChange={setMode} />
            <SearchBar
                onAnalyze={(t) => {
                    if (mode === 'quick') analyze(t);
                    else router.push(`/deep?ticker=${t}`);
                }}
                loading={loading}
                defaultValue={ticker}
            />

            {/* Error state with retry */}
            {error && (
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-4 rounded-xl text-sm fade-in"
                    style={{ background: 'rgba(239,68,68,0.08)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}>
                    <div className="flex items-center gap-2">
                        <AlertTriangle size={14} /> {error}
                    </div>
                    {ticker && (
                        <button onClick={() => analyze(ticker)}
                            className="flex items-center gap-1 text-xs font-semibold hover:opacity-80 transition-opacity">
                            <RefreshCw size={12} /> Retry
                        </button>
                    )}
                </div>
            )}

            {/* Results */}
            {(loading || d) && (
                <div id="analysis-root" ref={resultRef} className="space-y-4">

                    {/* Phase 17: Memory highlight */}
                    {!loading && d && (
                        <MemoryHighlightBanner memoryRecall={d.memory_recall as Parameters<typeof MemoryHighlightBanner>[0]['memoryRecall']} />
                    )}

                    {/* Phase 17: Executive summary banner */}
                    <ExecutiveSummaryBanner
                        ticker={ticker.toUpperCase()}
                        insights={d?.insights as Record<string, unknown>}
                        risk={d?.risk as Record<string, unknown>}
                        confidence={d?.confidence as Record<string, unknown>}
                        forecast={d?.forecast as Record<string, unknown>}
                        fundamentals={d?.fundamentals as Record<string, unknown>}
                        loading={loading}
                        demoMode={demoMode}
                        generatedAt={response?.generated_at}
                    />

                    {/* Market snapshot */}
                    <CompanySnapshot data={d?.market as Parameters<typeof CompanySnapshot>[0]['data']} loading={loading} />

                    {/* Risk + Confidence row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <RiskPanel data={d?.risk as Parameters<typeof RiskPanel>[0]['data']} loading={loading} />
                        <ConfidencePanel data={d?.confidence as Parameters<typeof ConfidencePanel>[0]['data']} loading={loading} />
                    </div>

                    {/* Insights */}
                    <InsightsPanel data={d?.insights as Parameters<typeof InsightsPanel>[0]['data']} loading={loading} />

                    {/* Phase 17: Recommendations + Transparency row */}
                    {!loading && d && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <SmartRecommendationPanel
                                ticker={ticker.toUpperCase()}
                                recommendations={recs}
                                insights={d?.insights as Record<string, unknown>}
                                loading={loading}
                            />
                            <TransparencyPanel
                                confidence={d?.confidence as Record<string, unknown>}
                                market={d?.market as Record<string, unknown>}
                            />
                        </div>
                    )}

                    {/* Phase 17: Export bar + freshness */}
                    {!loading && response && (
                        <div className="flex flex-col gap-3">
                            <ExportBar ticker={ticker.toUpperCase()} data={response} />
                            <DataFreshnessBar
                                generatedAt={response.generated_at}
                                executionTimeMs={response.execution_time_ms}
                                demoMode={demoMode}
                                cached={response.summary_type?.includes('cached')}
                            />
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

function QuickPageContent() {
    return (
        <DashboardLayout>
            <Suspense fallback={
                <div className="max-w-5xl mx-auto space-y-4">
                    <div className="skeleton h-12 rounded-xl" />
                    <div className="skeleton h-28 rounded-2xl" />
                    <div className="skeleton h-48 rounded-xl" />
                </div>
            }>
                <QuickContent />
            </Suspense>
        </DashboardLayout>
    );
}

export default function QuickPage() {
    return (
        <Suspense fallback={<DashboardLayout><div className="skeleton h-64 w-full rounded-xl" /></DashboardLayout>}>
            <QuickPageContent />
        </Suspense>
    );
}


