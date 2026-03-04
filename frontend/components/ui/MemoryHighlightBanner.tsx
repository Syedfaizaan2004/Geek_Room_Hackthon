// components/ui/MemoryHighlightBanner.tsx
// Phase 17 — Shows when prior analysis matches current research context.

'use client';
import { Sparkles, ExternalLink } from 'lucide-react';

interface MemoryEntry {
    ticker?: string;
    summary_excerpt?: string;
    risk_score?: number;
    similarity_score?: number;
}

interface MemoryHighlightBannerProps {
    memoryRecall?: MemoryEntry[] | { matches?: MemoryEntry[]; total_found?: number } | null;
}

export default function MemoryHighlightBanner({ memoryRecall }: MemoryHighlightBannerProps) {
    const matches = Array.isArray(memoryRecall) ? memoryRecall : (memoryRecall?.matches ?? []);
    if (!matches.length) return null;

    const top = matches[0];
    const simScore = top.similarity_score ? Math.round(top.similarity_score * 100) : null;

    return (
        <div className="memory-banner flex items-start gap-3 slide-in">
            <Sparkles size={16} style={{ color: '#818cf8', flexShrink: 0, marginTop: 2 }} />
            <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold" style={{ color: '#a5b4fc' }}>
                    Memory Match Found
                    {simScore !== null && (
                        <span className="ml-2 font-normal" style={{ color: 'rgba(255,255,255,0.4)' }}>
                            {simScore}% similar
                        </span>
                    )}
                </p>
                <p className="text-xs mt-0.5 leading-relaxed" style={{ color: 'rgba(255,255,255,0.6)' }}>
                    You previously analyzed similar risk patterns
                    {top.ticker ? ` (${top.ticker})` : ''}.{' '}
                    {top.summary_excerpt ? top.summary_excerpt.slice(0, 100) + '…' : ''}
                </p>
            </div>
            {top.ticker && (
                <button
                    onClick={() => window.location.href = `/quick?ticker=${top.ticker}`}
                    className="flex items-center gap-1 text-[11px] font-semibold flex-shrink-0"
                    style={{ color: '#818cf8' }}
                >
                    View <ExternalLink size={11} />
                </button>
            )}
        </div>
    );
}
