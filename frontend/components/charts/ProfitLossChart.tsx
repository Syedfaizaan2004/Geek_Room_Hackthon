// components/charts/ProfitLossChart.tsx
// Phase 17 — Profitability bar chart using fundamentals data.
// Fields: profitability.net_profit_margin, operating_margin, gross_margin, ebitda_margin
//         capital_efficiency.roe, roa
//         growth.revenue_growth_yoy, earnings_growth_yoy

'use client';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
    ReferenceLine, ResponsiveContainer, Cell
} from 'recharts';

interface ProfitLossChartProps {
    fundamentals?: Record<string, unknown>;
    ticker?: string;
    loading?: boolean;
}

function pct(v: unknown) {
    if (v == null) return null;
    return +(Number(v) * 100).toFixed(1);
}

function buildChartData(fund: Record<string, unknown>) {
    const prof = fund.profitability as Record<string, number | null> | undefined;
    const growth = fund.growth as Record<string, number | null> | undefined;
    const cap = fund.capital_efficiency as Record<string, number | null> | undefined;

    return [
        { name: 'Net Margin', value: pct(prof?.net_profit_margin), group: 'Margin' },
        { name: 'Op. Margin', value: pct(prof?.operating_margin), group: 'Margin' },
        { name: 'Gross Margin', value: pct(prof?.gross_margin), group: 'Margin' },
        { name: 'EBITDA Marg.', value: pct(prof?.ebitda_margin), group: 'Margin' },
        { name: 'Rev. Growth', value: pct(growth?.revenue_growth_yoy), group: 'Growth' },
        { name: 'EPS Growth', value: pct(growth?.earnings_growth_yoy), group: 'Growth' },
        { name: 'ROE', value: pct(cap?.roe), group: 'Returns' },
        { name: 'ROA', value: pct(cap?.roa), group: 'Returns' },
    ].filter(d => d.value !== null);
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number }>; label?: string }) => {
    if (!active || !payload?.length) return null;
    const val = payload[0].value;
    return (
        <div className="card text-xs p-3" style={{ border: '1px solid rgba(255,255,255,0.1)', minWidth: 130 }}>
            <p className="font-semibold text-white mb-1">{label}</p>
            <p style={{ color: val >= 0 ? '#10b981' : '#ef4444' }}>{val >= 0 ? '+' : ''}{val?.toFixed(1)}%</p>
        </div>
    );
};

export default function ProfitLossChart({ fundamentals, ticker = '', loading }: ProfitLossChartProps) {
    if (loading) return <div className="skeleton h-52 rounded-xl" />;
    if (!fundamentals || !fundamentals.profitability) return (
        <div className="flex items-center justify-center h-40 rounded-xl text-xs" style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)' }}>
            No fundamentals data available
        </div>
    );

    const chartData = buildChartData(fundamentals);
    const healthScore = Number(fundamentals.financial_health_score ?? 0);
    const classification = fundamentals.classification as string ?? 'unknown';
    const healthColor = classification === 'strong' ? '#10b981' : classification === 'moderate' ? '#f59e0b' : '#ef4444';

    return (
        <div className="card fade-in space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                    <h3 className="text-sm font-bold text-white">Financial Health & Profitability</h3>
                    <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                        {ticker} · Margins · Growth · Returns (TTM)
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-xs px-3 py-1 rounded-lg capitalize font-semibold"
                        style={{ background: `rgba(${healthColor === '#10b981' ? '16,185,129' : healthColor === '#f59e0b' ? '245,158,11' : '239,68,68'},0.15)`, color: healthColor }}>
                        {classification} · Score {healthScore.toFixed(0)}/100
                    </span>
                </div>
            </div>

            {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={210}>
                    <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                        <XAxis dataKey="name" tick={{ fill: '#64748b', fontSize: 9 }} axisLine={false} tickLine={false}
                            angle={-30} textAnchor="end" interval={0} />
                        <YAxis tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false}
                            tickFormatter={v => `${v}%`} width={40} />
                        <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                        <ReferenceLine y={0} stroke="rgba(255,255,255,0.15)" strokeWidth={1} />
                        <Bar dataKey="value" radius={[4, 4, 0, 0]} name="Value" maxBarSize={36}>
                            {chartData.map((d, i) => (
                                <Cell
                                    key={i}
                                    fill={(d.value ?? 0) >= 0 ? '#10b981' : '#ef4444'}
                                    fillOpacity={0.85}
                                />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            ) : (
                <div className="text-xs text-center py-8" style={{ color: 'var(--text-muted)' }}>
                    Financial data not available for this ticker
                </div>
            )}

            {/* Summary grid */}
            <div className="grid grid-cols-2 gap-2 pt-2" style={{ borderTop: '1px solid var(--border)' }}>
                {[
                    { label: 'Revenue Growth', value: pct((fundamentals.growth as Record<string, unknown>)?.revenue_growth_yoy), suffix: '%' },
                    { label: 'Earnings Growth', value: pct((fundamentals.growth as Record<string, unknown>)?.earnings_growth_yoy), suffix: '%' },
                    { label: 'Free Cash Flow', value: (fundamentals.cash_flow as Record<string, number>)?.free_cash_flow, prefix: '$', billions: true },
                    { label: 'FCF Margin', value: pct((fundamentals.cash_flow as Record<string, unknown>)?.fcf_margin), suffix: '%' },
                ].map(m => (
                    <div key={m.label} className="rounded-lg p-2" style={{ background: 'var(--bg-primary)' }}>
                        <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{m.label}</p>
                        <p className="text-xs font-bold"
                            style={{ color: m.value == null ? 'var(--text-muted)' : (typeof m.value === 'number' && m.value >= 0) ? '#10b981' : '#ef4444' }}>
                            {m.value == null ? '—' : m.billions && m.prefix
                                ? `${m.prefix}${(m.value / 1e9).toFixed(2)}B`
                                : `${m.value >= 0 ? '+' : ''}${m.value}${m.suffix ?? ''}`}
                        </p>
                    </div>
                ))}
            </div>

            <p className="text-[10px] text-center" style={{ color: 'rgba(255,255,255,0.2)' }}>
                Green = positive · Red = negative/loss · Based on trailing twelve months (TTM)
            </p>
        </div>
    );
}
