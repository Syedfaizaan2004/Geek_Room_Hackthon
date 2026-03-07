'use client';

import { useEffect, useMemo, useState } from 'react';
import { resolveTicker } from '@/services/agent';

const tickerNameCache = new Map<string, string>();

function normalizeTicker(ticker?: string | null): string {
    return (ticker ?? '').trim().toUpperCase();
}

type ResolvedState = {
    ticker: string;
    companyName: string | null;
};

export function useCompanyIdentity(ticker?: string | null) {
    const normalizedTicker = normalizeTicker(ticker);
    const cachedName = normalizedTicker ? (tickerNameCache.get(normalizedTicker) ?? null) : null;
    const [resolved, setResolved] = useState<ResolvedState>({ ticker: '', companyName: null });

    useEffect(() => {
        let active = true;

        if (!normalizedTicker || cachedName) {
            return () => {
                active = false;
            };
        }

        resolveTicker(normalizedTicker)
            .then((result) => {
                if (!active) return;
                const companyName = result?.company_name ?? null;
                if (companyName) {
                    tickerNameCache.set(normalizedTicker, companyName);
                }
                setResolved({ ticker: normalizedTicker, companyName });
            })
            .catch(() => {
                if (!active) return;
                setResolved({ ticker: normalizedTicker, companyName: null });
            });

        return () => {
            active = false;
        };
    }, [cachedName, normalizedTicker]);

    const companyName =
        cachedName ??
        (resolved.ticker === normalizedTicker ? resolved.companyName : null);

    const displayLabel = useMemo(() => {
        if (!normalizedTicker) return '';
        if (!companyName) return normalizedTicker;
        return `${companyName} (${normalizedTicker})`;
    }, [companyName, normalizedTicker]);

    return {
        ticker: normalizedTicker,
        companyName,
        displayLabel,
    };
}
