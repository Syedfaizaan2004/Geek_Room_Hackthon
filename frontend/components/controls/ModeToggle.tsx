'use client';
import { Zap, Brain } from 'lucide-react';

export type AnalysisMode = 'quick' | 'deep';

interface Props {
    mode: AnalysisMode;
    onChange: (mode: AnalysisMode) => void;
}

export default function ModeToggle({ mode, onChange }: Props) {
    return (
        <div className="flex flex-wrap gap-1 p-1 rounded-xl w-full sm:w-fit mb-3" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
            <button
                type="button"
                onClick={() => onChange('quick')}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
                style={mode === 'quick' ? { background: '#3b82f6', color: 'white' } : { color: 'var(--text-muted)' }}
            >
                <Zap size={14} /> Quick Mode
            </button>
            <button
                type="button"
                onClick={() => onChange('deep')}
                className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all"
                style={mode === 'deep' ? { background: '#8b5cf6', color: 'white' } : { color: 'var(--text-muted)' }}
            >
                <Brain size={14} /> Deep Mode
            </button>
        </div>
    );
}
