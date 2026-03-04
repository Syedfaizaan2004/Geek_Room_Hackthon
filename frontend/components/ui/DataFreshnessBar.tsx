// components/ui/DataFreshnessBar.tsx
// Phase 17 — Data freshness and source indicator strip.

'use client';

interface DataFreshnessBarProps {
    generatedAt?: string;
    executionTimeMs?: number;
    demoMode?: boolean;
    cached?: boolean;
}

export default function DataFreshnessBar({ generatedAt, executionTimeMs, demoMode, cached }: DataFreshnessBarProps) {
    const formatted = generatedAt
        ? new Date(generatedAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        : null;

    let dotClass = 'freshness-live';
    let statusLabel = 'Live Data';
    if (demoMode) { dotClass = 'freshness-demo'; statusLabel = 'Demo Mode'; }
    else if (cached) { dotClass = 'freshness-cached'; statusLabel = 'Cached Result'; }

    return (
        <div className="flex items-center justify-between px-1 fade-in"
            style={{ borderTop: '1px solid var(--border)', paddingTop: 8, marginTop: 4 }}>
            <div className="flex items-center gap-2">
                <span className={`freshness-dot ${dotClass}`} />
                <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>{statusLabel}</span>
                <span className="text-[10px]" style={{ color: 'rgba(255,255,255,0.2)' }}>•</span>
                <span className="text-[11px]" style={{ color: 'var(--text-muted)' }}>
                    yfinance · Deterministic engines
                </span>
            </div>
            <div className="flex items-center gap-3">
                {executionTimeMs !== undefined && (
                    <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        {executionTimeMs < 1000 ? `${executionTimeMs}ms` : `${(executionTimeMs / 1000).toFixed(1)}s`}
                    </span>
                )}
                {formatted && (
                    <span className="text-[11px]" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        {formatted}
                    </span>
                )}
            </div>
        </div>
    );
}
