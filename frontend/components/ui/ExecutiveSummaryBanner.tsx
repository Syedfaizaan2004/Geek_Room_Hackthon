// components/ui/ExecutiveSummaryBanner.tsx
// Phase 17 — Bold top-of-page executive summary banner.
// Color-coded outlook, risk badge, confidence score, forecast bias, health score.

'use client';
import { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Minus, ShieldAlert, Brain, Activity } from 'lucide-react';

interface ExecutiveSummaryBannerProps {
    ticker: string;
    insights?: Record<string, unknown>;
    risk?: Record<string, unknown>;
    confidence?: Record<string, unknown>;
    forecast?: Record<string, unknown>;
    fundamentals?: Record<string, unknown>;
    loading?: boolean;
    demoMode?: boolean;
    generatedAt?: string;
}

function getOutlook(risk?: Record<string, unknown>, forecast?: Record<string, unknown>) {
    const score = (risk?.composite_risk_score as number) ?? 50;
    const basedOn = forecast?.based_on as Record<string, unknown> | undefined;
    const trend =
        (basedOn?.trend_direction as string) ??
        (forecast?.trend_direction as string) ??
        (forecast?.trend as string) ??
        '';
    if (score < 40 || trend.includes('uptrend') || trend.includes('bull')) return 'bullish';
    if (score > 65 || trend.includes('bear') || trend.includes('down')) return 'bearish';
    return 'neutral';
}

function AnimatedNumber({ target }: { target: number }) {
    const [val, setVal] = useState(0);
    useEffect(() => {
        let start = 0;
        const step = target / 40;
        const timer = setInterval(() => {
            start += step;
            if (start >= target) { setVal(target); clearInterval(timer); }
            else setVal(Math.floor(start));
        }, 16);
        return () => clearInterval(timer);
    }, [target]);
    return <span className="num-counter">{val}</span>;
}

export default function ExecutiveSummaryBanner({
    ticker, insights, risk, confidence, forecast, fundamentals,
    loading, demoMode, generatedAt
}: ExecutiveSummaryBannerProps) {
    if (loading) return (
        <div className="skeleton h-28 rounded-2xl fade-in" />
    );
    if (!insights && !risk) return null;

    const outlook = getOutlook(risk, forecast);
    const riskScore = (risk?.composite_risk_score as number) ?? 0;
    const riskClass = (risk?.risk_classification as string) ?? 'moderate';
    const confScore = (confidence?.confidence_score as number) ?? 0;
    const healthScore =
        (fundamentals?.financial_health_score as number) ??
        (fundamentals?.health_score_composite as number) ??
        null;
    const summary = (insights?.executive_summary as string) ??
        (insights?.plain_language_summary as string) ??
        `${ticker} analysis complete.`;

    const outlookConfig = {
        bullish: {
            bannerClass: 'banner-bull',
            icon: <TrendingUp size={22} color="#10b981" />,
            label: 'Bullish Outlook',
            color: '#10b981',
        },
        bearish: {
            bannerClass: 'banner-bear',
            icon: <TrendingDown size={22} color="#ef4444" />,
            label: 'Bearish Outlook',
            color: '#ef4444',
        },
        neutral: {
            bannerClass: 'banner-neut',
            icon: <Minus size={22} color="#f59e0b" />,
            label: 'Neutral Outlook',
            color: '#f59e0b',
        },
    }[outlook];

    const riskBadgeClass =
        riskClass === 'low' ? 'risk-badge-low' :
            riskClass === 'high' ? 'risk-badge-high' : 'risk-badge-mod';

    return (
        <div className={`${outlookConfig.bannerClass} rounded-2xl p-5 fade-in`}>
            <div className="flex items-start justify-between gap-4 flex-wrap">
                {/* Left: outlook + summary */}
                <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className="mt-0.5 flex-shrink-0">{outlookConfig.icon}</div>
                    <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                            <h2 className="text-base font-bold text-white">{ticker} — {outlookConfig.label}</h2>
                            {demoMode && (
                                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                                    style={{ background: 'rgba(99,102,241,0.2)', color: '#818cf8' }}>
                                    DEMO
                                </span>
                            )}
                        </div>
                        <p className="text-sm leading-relaxed" style={{ color: 'rgba(255,255,255,0.7)', maxWidth: 680 }}>
                            {summary}
                        </p>
                        {generatedAt && (
                            <p className="text-[10px] mt-1.5" style={{ color: 'rgba(255,255,255,0.35)' }}>
                                Generated {new Date(generatedAt).toLocaleString()}
                            </p>
                        )}
                    </div>
                </div>

                {/* Right: metric pills */}
                <div className="flex items-center gap-2 flex-wrap flex-shrink-0">
                    {/* Risk badge */}
                    <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold ${riskBadgeClass}`}>
                        <ShieldAlert size={11} />
                        Risk: <AnimatedNumber target={Math.round(riskScore)} />/100
                    </div>

                    {/* Confidence */}
                    <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                        style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.3)' }}>
                        <Brain size={11} />
                        Conf: <AnimatedNumber target={Math.round(confScore)} />%
                    </div>

                    {/* Health if available */}
                    {healthScore !== null && (
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold"
                            style={{ background: 'rgba(16,185,129,0.12)', color: '#34d399', border: '1px solid rgba(16,185,129,0.25)' }}>
                            <Activity size={11} />
                            Health: <AnimatedNumber target={Math.round(healthScore)} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
