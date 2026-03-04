'use client';
import { useState, useEffect } from 'react';
import { getAIInsights } from '@/services/agent';
import { BrainCircuit, ChevronDown, ChevronUp, Loader2, Sparkles } from 'lucide-react';

interface Insight {
    question: string;
    answer: string;
}

interface Props {
    ticker: string;
    analysisData: Record<string, unknown>;
}

export default function AIInsightsPanel({ ticker, analysisData }: Props) {
    const [insights, setInsights] = useState<Insight[]>([]);
    const [loading, setLoading] = useState(true);
    const [provider, setProvider] = useState<string>('');
    const [openIndex, setOpenIndex] = useState<number | null>(0);

    useEffect(() => {
        let mounted = true;
        setLoading(true);
        getAIInsights(ticker, analysisData)
            .then((res) => {
                if (mounted) {
                    setInsights(res.insights || []);
                    setProvider(res.provider || 'system');
                    setLoading(false);
                }
            })
            .catch(() => {
                if (mounted) setLoading(false);
            });
        return () => { mounted = false; };
    }, [ticker, analysisData]);

    if (loading) {
        return (
            <div className="card">
                <div className="flex items-center gap-2 mb-4">
                    <BrainCircuit size={16} className="text-purple-400" />
                    <h3 className="text-sm font-bold text-white">AI Investment Insights</h3>
                    <div className="ml-auto flex items-center gap-2">
                        <Loader2 size={12} className="animate-spin text-purple-400" />
                        <span className="text-xs text-purple-400">Generating AI Q&A...</span>
                    </div>
                </div>
                <div className="space-y-3">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="rounded-xl p-4" style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
                            <div className="skeleton h-4 w-3/4 rounded mb-3" />
                            <div className="skeleton h-3 w-full rounded mb-2" />
                            <div className="skeleton h-3 w-5/6 rounded" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (!insights?.length) return null;

    return (
        <div className="card">
            <div className="flex items-center gap-2 mb-4">
                <Sparkles size={16} className="text-purple-400" />
                <h3 className="text-sm font-bold text-white">AI Investment Insights</h3>
                {provider !== 'deterministic' && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider"
                        style={{ background: 'rgba(168,85,247,0.15)', color: '#c084fc', border: '1px solid rgba(168,85,247,0.3)' }}>
                        Powered by {provider}
                    </span>
                )}
                {provider === 'deterministic' && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full font-semibold uppercase tracking-wider bg-gray-800 text-gray-400">
                        Rule-Based Fallback
                    </span>
                )}
            </div>

            <div className="space-y-2">
                {insights.map((item, idx) => {
                    const isOpen = openIndex === idx;
                    return (
                        <div key={idx} className="rounded-xl overflow-hidden transition-all duration-200"
                            style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)' }}>
                            <button
                                onClick={() => setOpenIndex(isOpen ? null : idx)}
                                className="w-full flex items-center justify-between p-3 text-left hover:bg-white/5 transition-colors"
                            >
                                <span className="text-sm font-medium text-white pr-4">{item.question}</span>
                                {isOpen ? <ChevronUp size={16} className="text-gray-400 shrink-0" /> : <ChevronDown size={16} className="text-gray-400 shrink-0" />}
                            </button>
                            <div className={`transition-all duration-300 ease-in-out ${isOpen ? 'max-h-96 opacity-100' : 'max-h-0 opacity-0 overflow-hidden'}`}>
                                <div className="p-3 pt-0 text-sm leading-relaxed" style={{ color: 'var(--text-muted)' }}>
                                    <div className="w-full h-px mb-3" style={{ background: 'var(--border)' }} />
                                    {item.answer}
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
