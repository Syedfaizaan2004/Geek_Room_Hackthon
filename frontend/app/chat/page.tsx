'use client';
import { useState, useRef, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { sendChatMessage, ChatProvider } from '@/services/chat';
import { Send, Bot, User } from 'lucide-react';

interface Message {
    role: 'user' | 'assistant';
    text: string;
    meta?: { llm_used: boolean; provider: string; tokens_used: number; estimated_cost: number };
}

export default function ChatPage() {
    const [messages, setMessages] = useState<Message[]>([
        { role: 'assistant', text: 'Hello! I am your AI financial research assistant. Ask me about any company you have analyzed, or a general investment question.' }
    ]);
    const [input, setInput] = useState('');
    const [ticker, setTicker] = useState('');
    const [provider, setProvider] = useState<ChatProvider>('gemini');
    const [loading, setLoading] = useState(false);
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const send = async () => {
        if (!input.trim() || loading) return;
        const userMsg: Message = { role: 'user', text: input };
        setMessages((m) => [...m, userMsg]);
        setInput('');
        setLoading(true);

        try {
            const res = await sendChatMessage(input, ticker || undefined, provider);
            setMessages((m) => [...m, {
                role: 'assistant',
                text: res.enhanced_text,
                meta: { llm_used: res.llm_used, provider: res.provider, tokens_used: res.tokens_used, estimated_cost: res.estimated_cost }
            }]);
        } catch {
            setMessages((m) => [...m, { role: 'assistant', text: '⚠ Failed to get a response. Please try again.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <DashboardLayout>
            <div className="max-w-3xl mx-auto flex flex-col h-[calc(100vh-6rem)] md:h-[calc(100vh-3rem)]">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(6,182,212,0.2)' }}>
                            <Bot size={16} style={{ color: '#06b6d4' }} />
                        </div>
                        <div>
                            <h1 className="text-xl font-bold text-white">AI Chat</h1>
                            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>Conversational research powered by LLM + memory recall</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2 w-full sm:w-auto">
                        <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())}
                            placeholder="Ticker context"
                            className="px-3 py-1.5 rounded-lg text-xs text-white outline-none flex-1 sm:flex-none sm:w-28"
                            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                        />
                        <select
                            value={provider}
                            onChange={(e) => setProvider(e.target.value as ChatProvider)}
                            className="px-3 py-1.5 rounded-lg text-xs text-white outline-none flex-1 sm:flex-none"
                            style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                            aria-label="Chat LLM provider"
                        >
                            <option value="gemini">Gemini</option>
                            <option value="groq">Groq</option>
                        </select>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-3 pr-1 mb-4">
                    {messages.map((msg, i) => (
                        <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                            <div className="flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center"
                                style={{ background: msg.role === 'user' ? 'var(--accent)' : 'rgba(6,182,212,0.2)' }}>
                                {msg.role === 'user' ? <User size={13} className="text-white" /> : <Bot size={13} style={{ color: '#06b6d4' }} />}
                            </div>
                            <div className="max-w-[92%] sm:max-w-[80%]">
                                <div className="rounded-2xl px-4 py-3 text-sm leading-relaxed"
                                    style={msg.role === 'user'
                                        ? { background: 'var(--accent)', color: 'white' }
                                        : { background: 'var(--bg-card)', color: 'var(--text-primary)', border: '1px solid var(--border)' }
                                    }>
                                    {msg.text}
                                </div>
                                {msg.meta && (
                                    <div className="flex gap-3 mt-1 px-1">
                                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                            {msg.meta.llm_used ? `✨ ${msg.meta.provider}` : '🔧 fallback'}
                                        </span>
                                        <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                                            {msg.meta.tokens_used} tokens · ${msg.meta.estimated_cost.toFixed(5)}
                                        </span>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {loading && (
                        <div className="flex gap-3">
                            <div className="w-7 h-7 rounded-full flex items-center justify-center" style={{ background: 'rgba(6,182,212,0.2)' }}>
                                <Bot size={13} style={{ color: '#06b6d4' }} />
                            </div>
                            <div className="rounded-2xl px-4 py-3" style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
                                <div className="flex gap-1.5 items-center" style={{ color: 'var(--text-muted)' }}>
                                    <div className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-1.5 h-1.5 rounded-full bg-current animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={bottomRef} />
                </div>

                {/* Input */}
                <div className="flex flex-col sm:flex-row gap-2">
                    <input value={input} onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && send()}
                        placeholder="Ask about any ticker, risk, or past analysis..."
                        className="flex-1 px-4 py-3 rounded-xl text-sm text-white outline-none"
                        style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                    />
                    <button onClick={send} disabled={!input.trim() || loading}
                        className="w-full sm:w-auto px-4 py-3 rounded-xl transition-all disabled:opacity-50 flex items-center justify-center"
                        style={{ background: 'var(--accent)' }}>
                        <Send size={16} className="text-white" />
                    </button>
                </div>
            </div>
        </DashboardLayout>
    );
}
