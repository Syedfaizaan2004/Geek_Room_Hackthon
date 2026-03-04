// components/ui/ConfidenceRing.tsx
// Phase 17 — SVG circular progress ring for confidence scores.
// Shows High / Moderate / Low confidence with tooltip.

'use client';
import { useEffect, useState } from 'react';

interface ConfidenceRingProps {
    score: number;           // 0–100
    size?: number;           // px, default 88
    strokeWidth?: number;    // default 8
    label?: string;
    showTooltip?: boolean;
}

function getLevel(score: number) {
    if (score >= 75) return { label: 'High Confidence', color: '#10b981' };
    if (score >= 50) return { label: 'Moderate Confidence', color: '#f59e0b' };
    return { label: 'Low Confidence', color: '#ef4444' };
}

export default function ConfidenceRing({
    score, size = 88, strokeWidth = 8, label, showTooltip = true
}: ConfidenceRingProps) {
    const [animated, setAnimated] = useState(0);
    const { label: levelLabel, color } = getLevel(score);

    const r = (size - strokeWidth) / 2;
    const circ = 2 * Math.PI * r;
    const offset = circ - (animated / 100) * circ;

    useEffect(() => {
        const timer = setTimeout(() => setAnimated(score), 100);
        return () => clearTimeout(timer);
    }, [score]);

    const ring = (
        <div className="flex flex-col items-center gap-2">
            <svg width={size} height={size} className="block" style={{ transform: 'rotate(-90deg)' }}>
                <circle
                    cx={size / 2} cy={size / 2} r={r}
                    strokeWidth={strokeWidth}
                    fill="none"
                    className="conf-ring-track"
                    stroke="rgba(255,255,255,0.07)"
                />
                <circle
                    cx={size / 2} cy={size / 2} r={r}
                    strokeWidth={strokeWidth}
                    fill="none"
                    stroke={color}
                    strokeDasharray={circ}
                    strokeDashoffset={offset}
                    className="conf-ring-fill"
                    strokeLinecap="round"
                />
                {/* Score text — counter-rotate to appear upright */}
                <text
                    x="50%" y="50%"
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="white"
                    fontSize={size * 0.22}
                    fontWeight="700"
                    style={{ transform: 'rotate(90deg)', transformOrigin: 'center', fontVariantNumeric: 'tabular-nums' }}
                >
                    {Math.round(animated)}%
                </text>
            </svg>
            <div className="text-center">
                <p className="text-[11px] font-semibold" style={{ color }}>{levelLabel}</p>
                {label && <p className="text-[10px] mt-0.5" style={{ color: 'var(--text-muted)' }}>{label}</p>}
            </div>
        </div>
    );

    if (!showTooltip) return ring;

    return (
        <div className="tooltip-wrap">
            {ring}
            <div className="tooltip-box">
                Confidence reflects data completeness and internal consistency.
                Higher completeness and fewer contradictions = higher confidence.
            </div>
        </div>
    );
}
