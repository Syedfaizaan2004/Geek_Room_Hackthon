'use client';
import { Suspense, useEffect, useState, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import DashboardLayout from '@/components/layout/DashboardLayout';
import SearchBar from '@/components/controls/SearchBar';
import ModeToggle, { AnalysisMode } from '@/components/controls/ModeToggle';
import CompanySnapshot from '@/components/panels/CompanySnapshot';
import RiskPanel from '@/components/panels/RiskPanel';
import ConfidencePanel from '@/components/panels/ConfidencePanel';
import InsightsPanel from '@/components/panels/InsightsPanel';
import AIInsightsPanel from '@/components/panels/AIInsightsPanel';
// Phase 17 UX components
import ExecutiveSummaryBanner from '@/components/ui/ExecutiveSummaryBanner';
import SmartRecommendationPanel from '@/components/ui/SmartRecommendationPanel';
import MemoryHighlightBanner from '@/components/ui/MemoryHighlightBanner';
import TransparencyPanel from '@/components/ui/TransparencyPanel';
import DataFreshnessBar from '@/components/ui/DataFreshnessBar';
import ExportBar from '@/components/ui/ExportBar';
// Phase 17 Charts
import StockPriceChart from '@/components/charts/StockPriceChart';
import ProfitLossChart from '@/components/charts/ProfitLossChart';
import { runAnalysis, AgentResponseData } from '@/services/agent';
import { Brain, AlertTriangle, ShieldAlert, RefreshCw, BarChart3, DollarSign } from 'lucide-react';

// ─── Typed helpers from real backend schemas ────────────────────────────────
type ForecastData = {
    current_price?: number;
    mid_projection?: number;
    projected_upper_bound?: number;
    projected_lower_bound?: number;
    expected_move_percent?: number;
    forecast_horizon_days?: number;
    based_on?: { trend_direction?: string };
};
type FundamentalsData = {
    financial_health_score?: number;
    classification?: string;
    profitability?: { net_profit_margin?: number; operating_margin?: number; gross_margin?: number; ebitda_margin?: number };
    leverage?: { debt_to_equity?: number; current_ratio?: number; debt_to_assets?: number; classification?: string };
    liquidity?: { current_ratio?: number; quick_ratio?: number };
};
type ScenarioItem = {
    scenario_type?: string;
    adjusted_risk_score?: number;
    adjusted_projection?: number;
    baseline_projection?: number;
    impact_analysis?: string;
};

function isScenarioItem(value: unknown): value is ScenarioItem {
    if (!value || typeof value !== 'object') return false;
    const obj = value as Record<string, unknown>;
    return (
        typeof obj.scenario_type === 'string' ||
        typeof obj.adjusted_risk_score === 'number' ||
        typeof obj.baseline_projection === 'number' ||
        typeof obj.adjusted_projection === 'number'
    );
}

function DeepPageContent() {
    const router = useRouter();
    const params = useSearchParams();
    const [ticker, setTicker] = useState(params.get('ticker') ?? '');
    const [mode, setMode] = useState<AnalysisMode>('deep');
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
            const res = await runAnalysis(t, 'deep');
            setData(res.data);
            setResponse(res);
            setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
        } catch (e: unknown) {
            const err = e as { response?: { data?: { detail?: string } } };
            setError(err?.response?.data?.detail ?? 'Deep analysis failed. Please try again.');
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
    const demoMode = !!(d?.demo_mode);
    const recs = d?.recommendations as Parameters<typeof SmartRecommendationPanel>[0]['recommendations'];
    const fore = d?.forecast as ForecastData | null;
    const fund = d?.fundamentals as FundamentalsData | null;
    const mkt = d?.market as Record<string, unknown> | null;

    // Scenario payload can be:
    // - a list of scenario objects (demo fixtures)
    // - a single scenario object (live deep mode)
    // - a map keyed by scenario name (legacy shape)
    const scenarioRaw = d?.scenario;
    const scenarios: ScenarioItem[] = (() => {
        if (!scenarioRaw) return [];
        if (Array.isArray(scenarioRaw)) return scenarioRaw as ScenarioItem[];
        if (isScenarioItem(scenarioRaw)) return [scenarioRaw];
        if (typeof scenarioRaw === 'object') {
            return Object.values(scenarioRaw as Record<string, unknown>)
                .filter(isScenarioItem);
        }
        return [];
    })();

    // Market moving averages from backend: market.moving_averages.sma_20, sma_50, sma_200
    const ma = (mkt?.moving_averages as Record<string, number | null> | undefined);
    const sma20 = ma?.sma_20;
    const sma50 = ma?.sma_50;

    // Fundamentals key metrics from nested schema
    const lev = fund?.leverage;
    const liq = fund?.liquidity;

    const healthScore = fund?.financial_health_score;
    const healthClass = fund?.classification ?? 'unknown';
    const healthColor = healthClass === 'strong' ? '#10b981' : healthClass === 'moderate' ? '#f59e0b' : '#ef4444';

    const Stat = ({ label, value, color }: { label: string; value?: string | number | null; color?: string }) => (
        <div className="rounded-lg p-3 card-hover" style={{ background: 'var(--bg-primary)' }}>
            <p className="text-xs mb-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>
            <p className="text-sm font-semibold" style={{ color: color ?? 'white' }}>{value ?? '—'}</p>
        </div>
    );

    return (
        <DashboardLayout>
            <div className="max-w-6xl mx-auto space-y-5">
                {/* Header */}
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(139,92,246,0.2)' }}>
                        <Brain size={16} style={{ color: '#8b5cf6' }} />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Deep Research</h1>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                            Full 8-engine pipeline · fundamentals · forecast · risk · scenario · comparison · LLM narrative
                        </p>
                    </div>
                </div>

                <ModeToggle mode={mode} onChange={setMode} />
                <SearchBar
                    onAnalyze={(t) => {
                        if (mode === 'deep') analyze(t);
                        else router.push(`/quick?ticker=${t}`);
                    }}
                    loading={loading}
                    defaultValue={ticker}
                />

                {/* Error + Retry */}
                {error && (
                    <div className="flex items-center justify-between p-4 rounded-xl text-sm fade-in"
                        style={{ background: 'rgba(239,68,68,0.08)', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)' }}>
                        <div className="flex items-center gap-2"><AlertTriangle size={14} />{error}</div>
                        {ticker && (
                            <button onClick={() => analyze(ticker)}
                                className="flex items-center gap-1 text-xs font-semibold hover:opacity-80 transition-opacity">
                                <RefreshCw size={12} /> Retry
                            </button>
                        )}
                    </div>
                )}

                {(loading || d) && (
                    <div id="analysis-root" ref={resultRef} className="space-y-4">

                        {/* Memory highlight */}
                        {!loading && d && (
                            <MemoryHighlightBanner memoryRecall={d.memory_recall as Parameters<typeof MemoryHighlightBanner>[0]['memoryRecall']} />
                        )}

                        {/* Executive banner */}
                        <ExecutiveSummaryBanner
                            ticker={ticker.toUpperCase()}
                            insights={d?.insights as Record<string, unknown>}
                            risk={d?.risk as Record<string, unknown>}
                            confidence={d?.confidence as Record<string, unknown>}
                            forecast={fore as Record<string, unknown>}
                            fundamentals={fund as Record<string, unknown>}
                            loading={loading}
                            demoMode={demoMode}
                            generatedAt={response?.generated_at}
                        />

                        {/* Market snapshot */}
                        <CompanySnapshot data={mkt as Parameters<typeof CompanySnapshot>[0]['data']} loading={loading} />

                        {/* ── SECTION: Financial Health ──────────────────────── */}
                        <div className="card">
                            <div className="flex items-center gap-2 mb-4">
                                <DollarSign size={14} style={{ color: '#10b981' }} />
                                <h3 className="text-sm font-bold text-white">Financial Health</h3>
                                {!loading && fund && (
                                    <span className="ml-auto text-xs px-2 py-0.5 rounded-lg capitalize font-semibold"
                                        style={{ background: `rgba(${healthColor === '#10b981' ? '16,185,129' : healthColor === '#f59e0b' ? '245,158,11' : '239,68,68'},0.15)`, color: healthColor }}>
                                        {healthClass} · {healthScore?.toFixed(0) ?? '—'}/100
                                    </span>
                                )}
                            </div>
                            {loading ? <div className="skeleton h-20 rounded-lg" /> : (
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                    <Stat label="Health Score"
                                        value={healthScore != null ? `${healthScore.toFixed(1)}/100` : null}
                                        color={healthColor} />
                                    <Stat label="Debt / Equity"
                                        value={lev?.debt_to_equity != null ? lev.debt_to_equity.toFixed(2) : null} />
                                    <Stat label="Current Ratio"
                                        value={liq?.current_ratio != null ? liq.current_ratio.toFixed(2) : null}
                                        color={!loading && (liq?.current_ratio ?? 0) >= 1.5 ? '#10b981' : (liq?.current_ratio ?? 0) >= 1 ? '#f59e0b' : '#ef4444'} />
                                    <Stat label="Leverage Class"
                                        value={lev?.classification ? lev.classification.charAt(0).toUpperCase() + lev.classification.slice(1) : null} />
                                </div>
                            )}
                        </div>

                        {/* ── SECTION: Price Forecast with MA20/MA50 ─────────── */}
                        <div className="card">
                            <div className="flex items-center gap-2 mb-4">
                                <BarChart3 size={14} style={{ color: '#3b82f6' }} />
                                <h3 className="text-sm font-bold text-white">Price Forecast</h3>
                                {!loading && fore && (
                                    <span className="ml-auto text-xs" style={{ color: 'var(--text-muted)' }}>
                                        {fore.forecast_horizon_days}-day horizon
                                    </span>
                                )}
                            </div>
                            {loading ? <div className="skeleton h-20 rounded-lg" /> : (
                                <>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-2">
                                        <Stat label="Current Price"
                                            value={fore?.current_price != null ? `$${fore.current_price.toFixed(2)}` : null} />
                                        <Stat label="Target (Mid)"
                                            value={fore?.mid_projection != null ? `$${fore.mid_projection.toFixed(2)}` : null}
                                            color={fore?.mid_projection && fore?.current_price && fore.mid_projection > fore.current_price ? '#10b981' : '#ef4444'} />
                                        <Stat label="MA20"
                                            value={sma20 != null ? `$${sma20.toFixed(2)}` : null}
                                            color="#f59e0b" />
                                        <Stat label="MA50"
                                            value={sma50 != null ? `$${sma50.toFixed(2)}` : null}
                                            color="#3b82f6" />
                                    </div>
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                                        <Stat label="Upside Bound"
                                            value={fore?.projected_upper_bound != null ? `$${fore.projected_upper_bound.toFixed(2)}` : null}
                                            color="#10b981" />
                                        <Stat label="Downside Bound"
                                            value={fore?.projected_lower_bound != null ? `$${fore.projected_lower_bound.toFixed(2)}` : null}
                                            color="#ef4444" />
                                        <Stat label="Expected Move"
                                            value={fore?.expected_move_percent != null ? `±${(fore.expected_move_percent * 100).toFixed(1)}%` : null} />
                                        <Stat label="Trend Bias"
                                            value={fore?.based_on?.trend_direction ?? 'N/A'} />
                                    </div>
                                </>
                            )}
                        </div>

                        {/* ── CHARTS: Stock Price + Profit/Loss ──────────────── */}
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-4">
                            <StockPriceChart
                                forecast={fore as Record<string, unknown>}
                                market={mkt as Record<string, unknown>}
                                ticker={ticker.toUpperCase()}
                                loading={loading}
                            />
                            <div id="growth-analysis">
                                <ProfitLossChart
                                    fundamentals={fund as Record<string, unknown>}
                                    ticker={ticker.toUpperCase()}
                                    loading={loading}
                                />
                            </div>
                        </div>

                        {/* ── SECTION: Scenario Stress Tests ─────────────────── */}
                        <div className="card">
                            <div className="flex items-center gap-2 mb-4">
                                <ShieldAlert size={14} style={{ color: '#f59e0b' }} />
                                <h3 className="text-sm font-bold text-white">Scenario Stress Tests</h3>
                                <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full font-semibold"
                                    style={{ background: 'rgba(245,158,11,0.12)', color: '#fbbf24' }}>
                                    DETERMINISTIC
                                </span>
                            </div>
                            {loading ? <div className="skeleton h-32 rounded-lg" /> :
                                scenarios.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                        {scenarios.map((sc, i) => {
                                            const rScore = sc.adjusted_risk_score ?? 0;
                                            const rClass = rScore > 70 ? 'risk-badge-high' : rScore > 45 ? 'risk-badge-mod' : 'risk-badge-low';
                                            const projShift = sc.adjusted_projection != null && sc.baseline_projection != null
                                                ? ((sc.adjusted_projection - sc.baseline_projection) / sc.baseline_projection * 100).toFixed(1)
                                                : null;
                                            return (
                                                <div key={i} className="rounded-xl p-3 space-y-2" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-xs font-semibold text-white capitalize">
                                                            {(sc.scenario_type ?? `Scenario ${i + 1}`).replace(/_/g, ' ')}
                                                        </span>
                                                        <span className={`text-[11px] font-bold px-2 py-0.5 rounded-lg ${rClass}`}>
                                                            Risk {rScore.toFixed(0)}
                                                        </span>
                                                    </div>
                                                    {projShift !== null && (
                                                        <p className="text-[11px]" style={{ color: Number(projShift) >= 0 ? '#10b981' : '#ef4444' }}>
                                                            Projection shift: {Number(projShift) >= 0 ? '+' : ''}{projShift}%
                                                        </p>
                                                    )}
                                                    {sc.impact_analysis && (
                                                        <p className="text-[11px] leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                                            {sc.impact_analysis.slice(0, 120)}{sc.impact_analysis.length > 120 ? '…' : ''}
                                                        </p>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                ) : (
                                    <p className="text-xs text-center py-6" style={{ color: 'var(--text-muted)' }}>
                                        Scenario data not available for this analysis
                                    </p>
                                )
                            }
                        </div>

                        {/* Risk + Confidence */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <RiskPanel data={d?.risk as Parameters<typeof RiskPanel>[0]['data']} loading={loading} />
                            <ConfidencePanel data={d?.confidence as Parameters<typeof ConfidencePanel>[0]['data']} loading={loading} />
                        </div>

                        {/* Insights */}
                        <InsightsPanel data={d?.insights as Parameters<typeof InsightsPanel>[0]['data']} loading={loading} />

                        {/* AI Insights (Gemini) */}
                        {!loading && d && (
                            <AIInsightsPanel ticker={ticker.toUpperCase()} analysisData={d as Record<string, unknown>} />
                        )}

                        {/* Recommendations + Transparency */}
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
                                    market={mkt as Record<string, unknown>}
                                />
                            </div>
                        )}

                        {/* Export + Freshness */}
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
        </DashboardLayout>
    );
}

export default function DeepPage() {
    return (
        <Suspense fallback={
            <DashboardLayout>
                <div className="max-w-6xl mx-auto space-y-5">
                    <div className="skeleton h-20 w-full rounded-xl" />
                    <div className="skeleton h-64 w-full rounded-xl" />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="skeleton h-48 rounded-xl" />
                        <div className="skeleton h-48 rounded-xl" />
                    </div>
                </div>
            </DashboardLayout>
        }>
            <DeepPageContent />
        </Suspense>
    );
}
