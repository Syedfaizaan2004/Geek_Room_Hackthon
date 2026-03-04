'use client';
import { useState, useEffect } from 'react';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { fetchPreferences, updatePreferences, PreferencesUpdate } from '@/services/preferences';
import { User, Save, CheckCircle } from 'lucide-react';

// ── Backend-matched field names ──────────────────────────────────────────────
// Backend PreferencesResponse: risk_tolerance | time_horizon | preferred_kpis | preferred_sectors
// Backend PreferencesUpdate:   risk_tolerance | time_horizon | preferred_kpis | preferred_sectors

const RISK_OPTIONS = ['conservative', 'moderate', 'aggressive'] as const;
const HORIZON_OPTIONS = ['short_term', 'medium_term', 'long_term'] as const;
const KPI_OPTIONS = ['pe_ratio', 'debt_to_equity', 'roe', 'revenue_growth', 'free_cash_flow', 'dividend_yield', 'current_ratio', 'ebitda'];
// Backend validator lowercases sectors — store and send lowercase
const SECTOR_OPTIONS = ['technology', 'healthcare', 'finance', 'energy', 'consumer', 'industrials', 'materials'];

type Prefs = {
    risk_tolerance?: string;
    time_horizon?: string;
    preferred_kpis?: string[];
    preferred_sectors?: string[];
};

export default function ProfilePage() {
    const [prefs, setPrefs] = useState<Prefs>({});
    const [saved, setSaved] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState('');

    useEffect(() => {
        fetchPreferences()
            .then((r) => setPrefs({
                risk_tolerance: r.risk_tolerance,
                time_horizon: r.time_horizon,
                preferred_kpis: r.preferred_kpis,
                preferred_sectors: r.preferred_sectors,
            }))
            .catch(() => { /* prefs may not exist yet */ })
            .finally(() => setLoading(false));
    }, []);

    const save = async () => {
        setSaving(true);
        setError('');
        try {
            const payload: PreferencesUpdate = {
                risk_tolerance: prefs.risk_tolerance as PreferencesUpdate['risk_tolerance'],
                time_horizon: prefs.time_horizon as PreferencesUpdate['time_horizon'],
                preferred_kpis: prefs.preferred_kpis,
                preferred_sectors: prefs.preferred_sectors,
            };
            await updatePreferences(payload);
            setSaved(true);
            setTimeout(() => setSaved(false), 3000);
        } catch {
            setError('Failed to save preferences. Please try again.');
        } finally {
            setSaving(false);
        }
    };

    const toggleKpi = (k: string) => setPrefs((p) => ({
        ...p,
        preferred_kpis: p.preferred_kpis?.includes(k)
            ? p.preferred_kpis.filter(x => x !== k)
            : [...(p.preferred_kpis ?? []), k]
    }));

    const toggleSector = (s: string) => setPrefs((p) => ({
        ...p,
        preferred_sectors: p.preferred_sectors?.includes(s)
            ? p.preferred_sectors.filter(x => x !== s)
            : [...(p.preferred_sectors ?? []), s]
    }));

    const ToggleChip = ({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) => (
        <button onClick={onClick}
            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all capitalize"
            style={active
                ? { background: 'rgba(59,130,246,0.2)', color: '#60a5fa', border: '1px solid rgba(59,130,246,0.4)' }
                : { background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }
            }>
            {label.replace(/_/g, ' ')}
        </button>
    );

    return (
        <DashboardLayout>
            <div className="max-w-2xl mx-auto space-y-6">
                <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.2)' }}>
                        <User size={16} style={{ color: '#6366f1' }} />
                    </div>
                    <h1 className="text-xl font-bold text-white">Profile &amp; Preferences</h1>
                </div>

                {loading ? <div className="skeleton h-64 rounded-xl" /> : (
                    <div className="card space-y-6">
                        {/* Risk Tolerance — matches backend field: risk_tolerance */}
                        <div>
                            <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>RISK TOLERANCE</label>
                            <div className="flex gap-2">
                                {RISK_OPTIONS.map((r) => (
                                    <button key={r} onClick={() => setPrefs(p => ({ ...p, risk_tolerance: r }))}
                                        className="flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-all"
                                        style={prefs.risk_tolerance === r
                                            ? { background: 'var(--accent)', color: 'white' }
                                            : { background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }
                                        }>
                                        {r}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Time Horizon */}
                        <div>
                            <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>TIME HORIZON</label>
                            <div className="flex gap-2">
                                {HORIZON_OPTIONS.map((h) => (
                                    <button key={h} onClick={() => setPrefs(p => ({ ...p, time_horizon: h }))}
                                        className="flex-1 py-2 rounded-lg text-sm font-medium transition-all"
                                        style={prefs.time_horizon === h
                                            ? { background: 'var(--accent)', color: 'white' }
                                            : { background: 'var(--bg-primary)', color: 'var(--text-muted)', border: '1px solid var(--border)' }
                                        }>
                                        {h.replace(/_/g, ' ')}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Preferred KPIs */}
                        <div>
                            <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>PREFERRED KPIs</label>
                            <div className="flex flex-wrap gap-2">
                                {KPI_OPTIONS.map((k) => (
                                    <ToggleChip key={k} label={k} active={prefs.preferred_kpis?.includes(k) ?? false} onClick={() => toggleKpi(k)} />
                                ))}
                            </div>
                        </div>

                        {/* Preferred Sectors — backend stores & returns lowercase */}
                        <div>
                            <label className="block text-xs font-semibold mb-2" style={{ color: 'var(--text-muted)' }}>PREFERRED SECTORS</label>
                            <div className="flex flex-wrap gap-2">
                                {SECTOR_OPTIONS.map((s) => (
                                    <ToggleChip key={s} label={s} active={prefs.preferred_sectors?.includes(s) ?? false} onClick={() => toggleSector(s)} />
                                ))}
                            </div>
                        </div>

                        {error && (
                            <p className="text-xs" style={{ color: '#ef4444' }}>{error}</p>
                        )}

                        <button onClick={save} disabled={saving}
                            className="w-full py-2.5 rounded-lg text-sm font-semibold text-white transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                            style={{ background: saved ? '#10b981' : 'var(--accent)' }}>
                            {saved ? <CheckCircle size={14} /> : <Save size={14} />}
                            {saving ? 'Saving...' : saved ? 'Saved!' : 'Save Preferences'}
                        </button>
                    </div>
                )}
            </div>
        </DashboardLayout>
    );
}
