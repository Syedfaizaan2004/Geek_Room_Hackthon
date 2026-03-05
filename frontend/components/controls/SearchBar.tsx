'use client';
import { useState, useCallback, useEffect, useRef } from 'react';
import { Search, Loader2 } from 'lucide-react';
import { suggestCompany, searchCompany } from '@/services/agent';

interface Props {
    onAnalyze: (ticker: string) => void;
    loading?: boolean;
    placeholder?: string;
    defaultValue?: string;
}

export default function SearchBar({ onAnalyze, loading, placeholder = 'Search company or enter ticker...', defaultValue = '' }: Props) {
    const [query, setQuery] = useState(defaultValue);
    const [suggestions, setSuggestions] = useState<{ ticker: string; company_name: string }[]>([]);
    const [showDropdown, setShowDropdown] = useState(false);
    const [debouncedQuery, setDebouncedQuery] = useState(defaultValue);
    const wrapperRef = useRef<HTMLDivElement>(null);
    const resetSuggestions = useCallback(() => {
        setSuggestions([]);
        setShowDropdown(false);
    }, []);

    // Debounce the query
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedQuery(query), 300);
        return () => clearTimeout(timer);
    }, [query]);

    // Fetch suggestions
    useEffect(() => {
        const normalized = debouncedQuery.trim();
        if (normalized.length < 2) {
            queueMicrotask(() => {
                setSuggestions([]);
                setShowDropdown(false);
            });
            return;
        }

        let active = true;
        suggestCompany(normalized)
            .then((res) => {
                if (!active) return;
                setSuggestions(res);
                setShowDropdown(true);
            })
            .catch(() => {
                if (!active) return;
                resetSuggestions();
            });

        return () => {
            active = false;
        };
    }, [debouncedQuery, resetSuggestions]);

    // Close dropdown on click outside
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
                setShowDropdown(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSubmit = useCallback(async (e: React.FormEvent) => {
        e.preventDefault();
        setShowDropdown(false);

        const raw = query.trim();
        if (!raw) return;

        const normalized = raw.toUpperCase();
        const exactSuggestion = suggestions.find(
            (item) =>
                item.ticker.toUpperCase() === normalized ||
                item.company_name.toLowerCase() === raw.toLowerCase()
        );
        if (exactSuggestion) {
            setQuery(exactSuggestion.ticker);
            onAnalyze(exactSuggestion.ticker);
            return;
        }

        // If there is a single strong suggestion, allow Enter to pick it.
        if (
            suggestions.length === 1 &&
            suggestions[0].ticker.toUpperCase() !== normalized &&
            suggestions[0].company_name.toLowerCase().includes(raw.toLowerCase())
        ) {
            const t = suggestions[0].ticker.toUpperCase();
            setQuery(t);
            onAnalyze(t);
            return;
        }

        // Resolve company names to ticker symbols; keep direct ticker input behavior unchanged.
        const looksLikeTicker = /^[A-Za-z][A-Za-z0-9.-]{0,9}$/.test(raw);
        const hasExactTickerSuggestion = suggestions.some((item) => item.ticker.toUpperCase() === normalized);
        const shouldResolveName =
            !looksLikeTicker ||
            raw !== raw.toUpperCase() ||
            raw.includes(' ') ||
            (suggestions.length > 0 && !hasExactTickerSuggestion);

        if (shouldResolveName) {
            const resolved = await searchCompany(raw);
            if (resolved?.ticker) {
                const t = resolved.ticker.toUpperCase();
                setQuery(t);
                onAnalyze(t);
                return;
            }
        }

        setQuery(normalized);
        onAnalyze(normalized);
    }, [query, suggestions, onAnalyze]);

    const handleSelect = (ticker: string) => {
        setQuery(ticker);
        setShowDropdown(false);
        onAnalyze(ticker);
    };

    return (
        <div className="relative w-full" ref={wrapperRef}>
            <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-2">
                <div className="relative flex-1">
                    <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }} />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => {
                            setQuery(e.target.value);
                            setShowDropdown(true);
                        }}
                        onFocus={() => { if (suggestions.length > 0) setShowDropdown(true); }}
                        placeholder={placeholder}
                        className="w-full pl-9 pr-3 py-3 rounded-xl text-sm text-white outline-none transition-all focus:ring-2 focus:ring-blue-500/50"
                        style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}
                    />
                </div>
                <button type="submit" disabled={!query.trim() || loading}
                    className="w-full sm:w-auto px-6 py-3 rounded-xl text-sm font-semibold text-white transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                    style={{ background: 'var(--accent)' }}>
                    {loading ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                    {loading ? 'Analyzing...' : 'Analyze'}
                </button>
            </form>

            {/* Suggestions Dropdown */}
            {showDropdown && suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 py-2 rounded-xl shadow-xl z-50 animate-in fade-in slide-in-from-top-2"
                    style={{ background: 'var(--bg-card)', border: '1px solid var(--border)' }}>
                    {suggestions.map((item) => (
                        <button
                            key={item.ticker}
                            type="button"
                            onClick={() => handleSelect(item.ticker)}
                            className="w-full text-left px-4 py-2 hover:bg-white/5 transition-colors flex items-center justify-between"
                        >
                            <span className="text-sm font-medium text-white">{item.company_name}</span>
                            <span className="text-xs font-semibold px-2 py-1 rounded bg-white/10 text-blue-400">
                                {item.ticker}
                            </span>
                        </button>
                    ))}
                </div>
            )}
        </div>
    );
}
