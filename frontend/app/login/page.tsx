'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { login, register } from '@/services/auth';
import { useAuthStore } from '@/store/authStore';
import { Brain, User, Hash, AlertCircle, CheckCircle, ShieldCheck, Activity, LineChart, Lock } from 'lucide-react';

type Mode = 'login' | 'register';

export default function LoginPage() {
    const [mode, setMode] = useState<Mode>('login');

    // Login fields
    const [uniqueId, setUniqueId] = useState('');
    const [dob, setDob] = useState('');

    // Extra register fields
    const [fullName, setFullName] = useState('');

    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const { login: storeLogin, hydrate, hydrated, isAuthenticated } = useAuthStore();
    const router = useRouter();

    useEffect(() => {
        hydrate();
    }, [hydrate]);

    useEffect(() => {
        if (hydrated && isAuthenticated) {
            router.replace('/');
        }
    }, [hydrated, isAuthenticated, router]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setLoading(true);
        try {
            if (mode === 'login') {
                const res = await login(uniqueId.trim().toLowerCase(), dob);
                storeLogin(res.access_token);
                router.push('/');
            } else {
                await register(fullName.trim(), uniqueId.trim().toLowerCase(), dob);
                setSuccess('Account created successfully! Please sign in.');
                setMode('login');
                setFullName('');
            }
        } catch (err: unknown) {
            const e = err as { response?: { data?: { detail?: string | { detail?: string } } } };
            const detail = e?.response?.data?.detail;
            setError(typeof detail === 'object' ? detail?.detail ?? 'Authentication failed.' : detail ?? 'Authentication failed.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center relative bg-[#0a0a0c] overflow-hidden font-sans">
            {/* Ambient Background Glows */}
            <div className="absolute inset-0 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] rounded-full opacity-20 Mix-blend-screen"
                    style={{ background: 'radial-gradient(circle, rgba(59,130,246,0.8) 0%, rgba(0,0,0,0) 70%)', filter: 'blur(80px)' }} />
                <div className="absolute bottom-[-10%] right-[-10%] w-[600px] h-[600px] rounded-full opacity-20 Mix-blend-screen"
                    style={{ background: 'radial-gradient(circle, rgba(139,92,246,0.8) 0%, rgba(0,0,0,0) 70%)', filter: 'blur(100px)' }} />
                <div className="absolute top-[40%] left-[60%] w-[300px] h-[300px] rounded-full opacity-10 Mix-blend-screen"
                    style={{ background: 'radial-gradient(circle, rgba(16,185,129,0.8) 0%, rgba(0,0,0,0) 70%)', filter: 'blur(60px)' }} />
            </div>

            {/* Grid Pattern Overlay */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
                style={{ backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            <div className="relative z-10 w-full max-w-[1000px] px-6 grid grid-cols-1 md:grid-cols-2 gap-12 items-center">

                {/* Left Side — Branding & Value Prop */}
                <div className="hidden md:flex flex-col justify-center space-y-8 pr-8">
                    <div>
                        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-6 shadow-2xl shadow-blue-500/20"
                            style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' }}>
                            <Brain size={32} className="text-white" />
                        </div>
                        <h1 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-white to-gray-400 mb-4 tracking-tight">
                            FinAgent Alpha
                        </h1>
                        <p className="text-gray-400 text-lg leading-relaxed max-w-sm">
                            Institutional-grade financial intelligence powered by an ensemble of multi-agent LLMs and deterministic quant engines.
                        </p>
                    </div>

                    <div className="space-y-5 mt-8">
                        {[
                            { icon: LineChart, text: "Real-time stochastic forecasting & price targets", color: "text-blue-400", bg: "bg-blue-500/10" },
                            { icon: ShieldCheck, text: "Deep multi-factor risk & scenario stress tests", color: "text-emerald-400", bg: "bg-emerald-500/10" },
                            { icon: Activity, text: "Natural language financial insights & Q&A", color: "text-purple-400", bg: "bg-purple-500/10" }
                        ].map((feature, idx) => (
                            <div key={idx} className="flex items-center gap-4 group">
                                <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-colors duration-300 ${feature.bg} group-hover:bg-white/10`}>
                                    <feature.icon size={18} className={feature.color} />
                                </div>
                                <span className="text-sm font-medium text-gray-300 group-hover:text-white transition-colors">{feature.text}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Side — Auth Card (Glassmorphism) */}
                <div className="w-full max-w-md mx-auto relative group">
                    {/* Glowing card border effect */}
                    <div className="absolute -inset-[1px] rounded-3xl bg-gradient-to-b from-white/15 to-white/5 opacity-50 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />

                    <div className="relative rounded-3xl p-8 backdrop-blur-xl bg-[#111116]/80 shadow-2xl"
                        style={{ boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 0 0 rgba(255, 255, 255, 0.05)' }}>

                        {/* Mobile Logo */}
                        <div className="md:hidden text-center mb-6">
                            <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-3 shadow-lg" style={{ background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)' }}>
                                <Brain size={24} className="text-white" />
                            </div>
                            <h2 className="text-xl font-bold text-white tracking-tight">FinAgent Alpha</h2>
                        </div>

                        {/* Mode Switcher */}
                        <div className="flex p-1.5 rounded-2xl bg-black/40 mb-8 border border-white/5 relative">
                            <div className="absolute inset-y-1.5 w-[calc(50%-6px)] rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 transition-transform duration-300 ease-out shadow-lg"
                                style={{ transform: mode === 'login' ? 'translateX(0)' : 'translateX(100%)' }} />

                            {(['login', 'register'] as Mode[]).map((m) => (
                                <button key={m} onClick={() => { setMode(m); setError(''); setSuccess(''); }}
                                    className={`relative z-10 flex-1 py-2.5 rounded-xl text-sm font-semibold transition-colors duration-200 
                                        ${mode === m ? 'text-white' : 'text-gray-400 hover:text-gray-200'}`}>
                                    {m === 'login' ? 'Sign In' : 'Create Account'}
                                </button>
                            ))}
                        </div>

                        <form onSubmit={handleSubmit} className="space-y-5 relative">

                            {/* Full Name */}
                            <div className={`transition-all duration-300 overflow-hidden ${mode === 'register' ? 'max-h-24 opacity-100 mb-5' : 'max-h-0 opacity-0 mb-0'}`}>
                                <label className="block text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-2 ml-1">Full Name</label>
                                <div className="relative group/input">
                                    <div className="absolute inset-0 rounded-xl transition-colors duration-200 bg-white/5 group-focus-within/input:bg-blue-500/10" />
                                    <User size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within/input:text-blue-400 transition-colors" />
                                    <input type="text" required={mode === 'register'} value={fullName} onChange={(e) => setFullName(e.target.value)}
                                        placeholder="Alice Johnson" minLength={3}
                                        className="w-full relative bg-transparent pl-11 pr-4 py-3.5 rounded-xl text-sm text-white placeholder-gray-600 outline-none border border-white/10 focus:border-blue-500/50 transition-all shadow-inner"
                                    />
                                </div>
                            </div>

                            {/* User ID */}
                            <div>
                                <label className="block text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-2 ml-1">
                                    Unique User ID <span className="text-gray-600 normal-case tracking-normal ml-1 font-medium">(Letters, digits, _ or -)</span>
                                </label>
                                <div className="relative group/input">
                                    <div className="absolute inset-0 rounded-xl transition-colors duration-200 bg-white/5 group-focus-within/input:bg-blue-500/10" />
                                    <Hash size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within/input:text-blue-400 transition-colors" />
                                    <input type="text" required value={uniqueId} onChange={(e) => setUniqueId(e.target.value)}
                                        placeholder="alice_fin_007" minLength={5} maxLength={50} pattern="[a-zA-Z0-9_-]+"
                                        className="w-full relative bg-transparent pl-11 pr-4 py-3.5 rounded-xl text-sm text-white placeholder-gray-600 outline-none border border-white/10 focus:border-blue-500/50 transition-all shadow-inner"
                                    />
                                </div>
                            </div>

                            {/* Password / DOB */}
                            <div>
                                <label className="block text-[11px] font-bold uppercase tracking-wider text-gray-400 mb-2 ml-1">
                                    Authentication Key <span className="text-gray-600 normal-case tracking-normal ml-1 font-medium">(Date of Birth)</span>
                                </label>
                                <div className="relative group/input">
                                    <div className="absolute inset-0 rounded-xl transition-colors duration-200 bg-white/5 group-focus-within/input:bg-blue-500/10" />
                                    <Lock size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within/input:text-blue-400 transition-colors" />
                                    <input type="date" required value={dob} onChange={(e) => setDob(e.target.value)}
                                        className="w-full relative bg-transparent pl-11 pr-4 py-3.5 rounded-xl text-sm text-white placeholder-gray-600 outline-none border border-white/10 focus:border-blue-500/50 transition-all shadow-inner"
                                        style={{ colorScheme: 'dark' }}
                                    />
                                </div>
                            </div>

                            {/* Error */}
                            {error && (
                                <div className="flex items-start gap-2.5 p-3.5 rounded-xl animate-in fade-in slide-in-from-top-1"
                                    style={{ background: 'linear-gradient(to right, rgba(239,68,68,0.1), rgba(239,68,68,0.05))', border: '1px solid rgba(239,68,68,0.2)' }}>
                                    <AlertCircle size={16} className="text-red-400 mt-0.5 shrink-0" />
                                    <span className="text-sm font-medium text-red-300 leading-snug">{error}</span>
                                </div>
                            )}

                            {/* Success */}
                            {success && (
                                <div className="flex items-start gap-2.5 p-3.5 rounded-xl animate-in fade-in slide-in-from-top-1"
                                    style={{ background: 'linear-gradient(to right, rgba(16,185,129,0.1), rgba(16,185,129,0.05))', border: '1px solid rgba(16,185,129,0.2)' }}>
                                    <CheckCircle size={16} className="text-emerald-400 mt-0.5 shrink-0" />
                                    <span className="text-sm font-medium text-emerald-300 leading-snug">{success}</span>
                                </div>
                            )}

                            {/* Submit Button */}
                            <button type="submit" disabled={loading}
                                className="w-full relative py-4 mt-6 rounded-xl text-sm font-bold text-white transition-all overflow-hidden group/btn disabled:opacity-70 disabled:cursor-not-allowed">
                                <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-600 transition-transform duration-300 group-hover/btn:scale-[1.02]" />
                                <div className="absolute inset-0 opacity-0 group-hover/btn:opacity-20 bg-white transition-opacity duration-300" />
                                <span className="relative flex items-center justify-center gap-2">
                                    {loading ? (
                                        <><Activity size={16} className="animate-spin" /> Authenticating...</>
                                    ) : (
                                        mode === 'login' ? 'Secure Access securely' : 'Initialize Account Profile'
                                    )}
                                </span>
                            </button>

                            <p className="text-center text-xs text-gray-500 font-medium mt-4">
                                End-to-end encrypted protocol.
                            </p>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}
