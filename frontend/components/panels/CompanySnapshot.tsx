'use client';
import { TrendingUp, TrendingDown, DollarSign, Activity, AlertTriangle } from 'lucide-react';

interface Props {
    data: {
        ticker?: string;
        company_name?: string;
        last_price?: number;
        price_change_percent?: number;
        volatility_percent?: number;
        change_pct?: number;
        volatility?: number;
        trend_direction?: string;
        sector?: string;
        volume?: number;
    } | null;
    loading?: boolean;
}

export default function CompanySnapshot({ data, loading }: Props) {
    if (loading) return (
        <div className="card">
            <div className="space-y-3">
                <div className="skeleton h-6 w-40" />
                <div className="skeleton h-10 w-28" />
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {[1, 2, 3].map(i => <div key={i} className="skeleton h-16 rounded-lg" />)}
                </div>
            </div>
        </div>
    );

    if (!data) return null;

    const changePct = data.price_change_percent ?? data.change_pct ?? 0;
    const volatility = data.volatility_percent ?? data.volatility ?? 0;
    const isUp = changePct >= 0;
    const TrendIcon = isUp ? TrendingUp : TrendingDown;

    return (
        <div className="card">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-4">
                <div>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl font-bold text-white">{data.ticker}</span>
                        <span className="badge badge-blue">{data.sector ?? 'N/A'}</span>
                    </div>
                    <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{data.company_name}</p>
                </div>
                <div className="sm:text-right">
                    <div className="flex items-center gap-1 sm:justify-end">
                        <DollarSign size={16} style={{ color: 'var(--text-muted)' }} />
                        <span className="text-3xl font-bold text-white">{(data.last_price ?? 0).toFixed(2)}</span>
                    </div>
                    <div className={`flex items-center gap-1 sm:justify-end text-sm font-medium mt-0.5 ${isUp ? 'text-green-400' : 'text-red-400'}`}>
                        <TrendIcon size={14} />
                        {isUp ? '+' : ''}{changePct.toFixed(2)}%
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Metric label="Trend" value={data.trend_direction ?? 'N/A'} icon={<Activity size={13} />} />
                <Metric label="Volatility" value={`${(volatility * 100).toFixed(1)}%`} icon={<AlertTriangle size={13} />} />
                <Metric label="Volume" value={data.volume ? `${(data.volume / 1_000_000).toFixed(1)}M` : 'N/A'} icon={<TrendingUp size={13} />} />
            </div>
        </div>
    );
}

function Metric({ label, value, icon }: { label: string; value: string; icon: React.ReactNode }) {
    return (
        <div className="rounded-lg p-3" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
            <div className="flex items-center gap-1.5 mb-1" style={{ color: 'var(--text-muted)' }}>
                {icon}
                <span className="text-xs">{label}</span>
            </div>
            <p className="text-sm font-semibold text-white">{value}</p>
        </div>
    );
}
