// components/ui/SmartRecommendationPanel.tsx
// Phase 17 — Suggested next-step recommendation cards with actionable buttons.

'use client';
import { useRouter } from 'next/navigation';
import { ArrowRight, BarChart2, ShieldAlert, Plus, Brain, Search, TrendingUp } from 'lucide-react';

interface Action {
    action_type: string;
    explanation: string;
}

interface SmartRecommendationPanelProps {
    ticker: string;
    recommendations?: {
        next_actions?: Action[];
        similar_companies?: Array<{ ticker: string }>;
        memory_reminders?: string[];
        watchlist_recommendations?: Array<{ ticker: string; reason?: string }>;
        behavioral_profile?: { engagement_pattern?: string };
    } | null;
    insights?: Record<string, unknown>;
    loading?: boolean;
}

const ACTION_ICONS: Record<string, React.ReactNode> = {
    scenario_stress_test: <ShieldAlert size={14} />,
    hidden_risk_scan: <ShieldAlert size={14} />,
    peer_comparison: <BarChart2 size={14} />,
    growth_analysis: <TrendingUp size={14} />,
    fundamental_review: <Search size={14} />,
    add_to_watchlist: <Plus size={14} />,
    deep_analysis: <Brain size={14} />,
    default: <ArrowRight size={14} />,
};

function getIcon(type: string) {
    return ACTION_ICONS[type] ?? ACTION_ICONS.default;
}

function actionUrl(ticker: string, type: string) {
    const map: Record<string, string> = {
        peer_comparison: `/compare?ticker=${ticker}`,
        scenario_stress_test: `/scenario?ticker=${ticker}&type=recession`,
        hidden_risk_scan: `/risk?ticker=${ticker}`,
        growth_analysis: `/deep?ticker=${ticker}#growth-analysis`,
        fundamental_review: `/deep?ticker=${ticker}`,
        add_to_watchlist: `/watchlists?ticker=${ticker}`,
        deep_analysis: `/deep?ticker=${ticker}`,
    };
    return map[type] ?? `/quick?ticker=${ticker}`;
}

export default function SmartRecommendationPanel({
    ticker, recommendations, insights, loading
}: SmartRecommendationPanelProps) {
    const router = useRouter();

    if (loading) return <div className="skeleton h-32 rounded-2xl fade-in" />;

    // Build action list — from recs or fallback from insights
    const actions: Action[] = recommendations?.next_actions?.length
        ? recommendations.next_actions.slice(0, 4)
        : [
            { action_type: 'peer_comparison', explanation: 'Compare with industry peers for relative valuation.' },
            { action_type: 'scenario_stress_test', explanation: 'Run scenario stress tests for downside protection.' },
            { action_type: 'add_to_watchlist', explanation: 'Add to watchlist for ongoing monitoring.' },
        ];

    const reminders = recommendations?.memory_reminders ?? [];
    const topRec = actions[0]?.explanation
        ?? (insights?.plain_language_summary as string)
        ?? null;

    return (
        <div className="card fade-in space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-white">Suggested Next Steps</h3>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full"
                    style={{ background: 'rgba(59,130,246,0.15)', color: '#60a5fa' }}>
                    AI GUIDED
                </span>
            </div>

            {topRec && (
                <p className="text-xs leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                    {topRec}
                </p>
            )}

            <div className="grid grid-cols-1 gap-2">
                {actions.map((a, i) => (
                    <button key={i}
                        onClick={() => router.push(actionUrl(ticker, a.action_type))}
                        className="w-full text-left flex items-center gap-3 px-4 py-3 rounded-xl transition-all card-hover"
                        style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}
                    >
                        <span style={{ color: '#6366f1' }} className="flex-shrink-0">
                            {getIcon(a.action_type)}
                        </span>
                        <span className="flex-1 min-w-0">
                            <span className="text-xs font-semibold text-white capitalize block">
                                {a.action_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-[11px] block truncate" style={{ color: 'var(--text-muted)' }}>
                                {a.explanation}
                            </span>
                        </span>
                        <ArrowRight size={12} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                    </button>
                ))}
            </div>

            {reminders.length > 0 && (
                <div className="pt-2 border-t" style={{ borderColor: 'var(--border)' }}>
                    <p className="text-[10px] font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>MEMORY REMINDERS</p>
                    {reminders.slice(0, 2).map((r, i) => (
                        <p key={i} className="text-xs mb-1" style={{ color: '#a5b4fc' }}>• {r}</p>
                    ))}
                </div>
            )}
        </div>
    );
}
