// components/charts/StockPriceChart.tsx
// Phase 17 — Stock price forecast chart using Recharts.
// Uses forecast data: current_price, mid_projection, projected_upper/lower_bound
// Uses market data: moving_averages.sma_20, sma_50

'use client';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
    ReferenceLine, ResponsiveContainer, Legend
} from 'recharts';

interface StockPriceChartProps {
    forecast?: Record<string, unknown>;
    market?: Record<string, unknown>;
    ticker?: string;
    loading?: boolean;
}

function fmt(v: unknown) {
    if (v == null) return '—';
    return `$${Number(v).toFixed(2)}`;
}

// Build a simple 5-point projection series from forecast data
function buildChartData(forecast: Record<string, unknown>, sma20?: number, sma50?: number) {
    const current = Number(forecast.current_price ?? 0);
    const mid = Number(forecast.mid_projection ?? current);
    const upper = Number(forecast.projected_upper_bound ?? mid * 1.05);
    const lower = Number(forecast.projected_lower_bound ?? mid * 0.95);
    const days = Number(forecast.forecast_horizon_days ?? 90);

    return [
        { day: 'Now', price: current, upper: current, lower: current, sma20, sma50 },
        { day: `Day ${Math.round(days * 0.25)}`, price: current + (mid - current) * 0.25, upper: current + (upper - current) * 0.25, lower: current + (lower - current) * 0.25 },
        { day: `Day ${Math.round(days * 0.5)}`, price: current + (mid - current) * 0.5, upper: current + (upper - current) * 0.5, lower: current + (lower - current) * 0.5 },
        { day: `Day ${Math.round(days * 0.75)}`, price: current + (mid - current) * 0.75, upper: current + (upper - current) * 0.75, lower: current + (lower - current) * 0.75 },
        { day: `Day ${days}`, price: mid, upper, lower },
    ].map(d => ({
        ...d,
        price: +d.price.toFixed(2),
        upper: +d.upper.toFixed(2),
        lower: +d.lower.toFixed(2),
    }));
}

const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; name: string; color: string }>; label?: string }) => {
    if (!active || !payload?.length) return null;
    return (
        <div className="card text-xs p-3 space-y-1" style={{ minWidth: 140, border: '1px solid rgba(255,255,255,0.1)' }}>
            <p className="font-semibold text-white mb-2">{label}</p>
            {payload.map((p, i) => (
                <div key={i} className="flex justify-between gap-4">
                    <span style={{ color: p.color }}>{p.name}</span>
                    <span className="text-white font-mono">${p.value?.toFixed(2)}</span>
                </div>
            ))}
        </div>
    );
};

export default function StockPriceChart({ forecast, market, ticker = '', loading }: StockPriceChartProps) {
    if (loading) return <div className="skeleton h-52 rounded-xl" />;
    if (!forecast || !forecast.current_price) return (
        <div className="flex items-center justify-center h-40 rounded-xl text-xs" style={{ background: 'var(--bg-primary)', color: 'var(--text-muted)' }}>
            No forecast data available
        </div>
    );

    const ma = (market?.moving_averages as Record<string, number> | undefined);
    const sma20 = ma?.sma_20;
    const sma50 = ma?.sma_50;
    const chartData = buildChartData(forecast, sma20, sma50);

    const current = Number(forecast.current_price);
    const mid = Number(forecast.mid_projection ?? current);
    const upper = Number(forecast.projected_upper_bound ?? mid);
    const lower = Number(forecast.projected_lower_bound ?? mid);
    const movePercent = ((forecast.expected_move_percent as number) ?? 0) * 100;
    const bias = mid > current ? 'bullish' : mid < current ? 'bearish' : 'neutral';
    const biasColor = bias === 'bullish' ? '#10b981' : bias === 'bearish' ? '#ef4444' : '#f59e0b';

    const yMin = Math.floor(Math.min(lower, sma50 ?? lower) * 0.97);
    const yMax = Math.ceil(Math.max(upper, sma20 ?? upper) * 1.03);

    return (
        <div className="card fade-in space-y-4">
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div>
                    <h3 className="text-sm font-bold text-white">Stock Price Forecast</h3>
                    <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                        {ticker} · {forecast.forecast_horizon_days as number}-day projection · Expected move: {movePercent.toFixed(1)}%
                    </p>
                </div>
                <div className="flex gap-2 flex-wrap">
                    <span className="text-xs px-2 py-1 rounded-lg" style={{ background: 'rgba(255,255,255,0.05)', color: 'var(--text-muted)' }}>
                        Now: <strong className="text-white">{fmt(current)}</strong>
                    </span>
                    <span className="text-xs px-2 py-1 rounded-lg capitalize" style={{ background: `rgba(${biasColor === '#10b981' ? '16,185,129' : biasColor === '#ef4444' ? '239,68,68' : '245,158,11'},0.12)`, color: biasColor }}>
                        {bias} · Target {fmt(mid)}
                    </span>
                </div>
            </div>

            {/* Key metrics row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                {[
                    { label: 'Current', value: fmt(current), color: '#94a3b8' },
                    { label: 'Target', value: fmt(mid), color: biasColor },
                    { label: 'Upside', value: fmt(upper), color: '#10b981' },
                    { label: 'Downside', value: fmt(lower), color: '#ef4444' },
                ].map(m => (
                    <div key={m.label} className="rounded-lg p-2 text-center" style={{ background: 'var(--bg-primary)' }}>
                        <p className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{m.label}</p>
                        <p className="text-xs font-bold font-mono" style={{ color: m.color }}>{m.value}</p>
                    </div>
                ))}
            </div>

            {/* Chart */}
            <ResponsiveContainer width="100%" height={200}>
                <AreaChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <defs>
                        <linearGradient id="uncertaintyBand" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#6366f1" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="midLine" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={biasColor} stopOpacity={0.25} />
                            <stop offset="95%" stopColor={biasColor} stopOpacity={0} />
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis domain={[yMin, yMax]} tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false}
                        tickFormatter={v => `$${v}`} width={54} />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: 11, color: '#64748b' }} />

                    {/* Uncertainty band — upper/lower area */}
                    <Area type="monotone" dataKey="upper" stroke="#6366f1" strokeWidth={1} strokeDasharray="4 2"
                        fill="url(#uncertaintyBand)" name="Upper Bound" />
                    <Area type="monotone" dataKey="lower" stroke="rgba(99,102,241,0.4)" strokeWidth={1} strokeDasharray="4 2"
                        fill="white" fillOpacity={0} name="Lower Bound" />

                    {/* Mid projection */}
                    <Area type="monotone" dataKey="price" stroke={biasColor} strokeWidth={2.5}
                        fill="url(#midLine)" name="Mid Projection" dot={{ r: 3, fill: biasColor }} activeDot={{ r: 5 }} />

                    {/* MA reference lines */}
                    {sma20 != null && <ReferenceLine y={sma20} stroke="#f59e0b" strokeDasharray="3 2"
                        label={{ value: `MA20 $${sma20.toFixed(0)}`, fill: '#f59e0b', fontSize: 10, position: 'insideTopRight' }} />}
                    {sma50 != null && <ReferenceLine y={sma50} stroke="#3b82f6" strokeDasharray="3 2"
                        label={{ value: `MA50 $${sma50.toFixed(0)}`, fill: '#3b82f6', fontSize: 10, position: 'insideTopRight' }} />}
                </AreaChart>
            </ResponsiveContainer>

            <p className="text-[10px] text-center" style={{ color: 'rgba(255,255,255,0.2)' }}>
                Shaded band = uncertainty range · Dashed lines = moving averages · Deterministic projection
            </p>
        </div>
    );
}
