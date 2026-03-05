'use client';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
    LayoutDashboard, Zap, Brain, GitCompare, ShieldAlert,
    BarChart3, Star, BookOpen, User, MessageSquare, Database, LogOut, Menu, X
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';

const navItems = [
    { href: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { href: '/quick', icon: Zap, label: 'Quick Analysis' },
    { href: '/deep', icon: Brain, label: 'Deep Research' },
    { href: '/compare', icon: GitCompare, label: 'Compare' },
    { href: '/risk', icon: ShieldAlert, label: 'Risk Overview' },
    { href: '/scenario', icon: BarChart3, label: 'Scenarios' },
    { href: '/watchlists', icon: Star, label: 'Recommendations' },
    { href: '/saved', icon: BookOpen, label: 'Saved Analyses' },
    { href: '/memory', icon: Database, label: 'Memory Search' },
    { href: '/chat', icon: MessageSquare, label: 'AI Chat' },
    { href: '/profile', icon: User, label: 'Profile & Prefs' },
];

function Brand() {
    return (
        <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--accent)' }}>
                <Brain size={16} className="text-white" />
            </div>
            <div>
                <p className="text-sm font-bold text-white">FinAgent</p>
                <p className="text-xs" style={{ color: 'var(--text-muted)' }}>AI Research Platform</p>
            </div>
        </div>
    );
}

function NavLinks({
    pathname,
    onNavigate,
}: {
    pathname: string;
    onNavigate?: () => void;
}) {
    return (
        <>
            {navItems.map(({ href, icon: Icon, label }) => {
                const isActive = pathname === href;
                return (
                    <Link
                        key={href}
                        href={href}
                        onClick={onNavigate}
                        className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                        style={isActive
                            ? { background: 'rgba(59,130,246,0.15)', color: '#60a5fa', borderLeft: '3px solid #3b82f6' }
                            : { color: 'var(--text-muted)' }}
                    >
                        <Icon size={16} />
                        <span>{label}</span>
                    </Link>
                );
            })}
        </>
    );
}

function LogoutButton({ onLogout }: { onLogout: () => void }) {
    return (
        <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:bg-red-500/10"
            style={{ color: 'var(--text-muted)' }}
        >
            <LogOut size={16} />
            <span>Logout</span>
        </button>
    );
}

export default function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuthStore();
    const router = useRouter();
    const [mobileOpen, setMobileOpen] = useState(false);

    const handleLogout = () => {
        logout();
        setMobileOpen(false);
        router.replace('/login');
    };

    const closeMobile = () => setMobileOpen(false);

    return (
        <>
            <header
                className="md:hidden px-4 py-3 border-b flex items-center justify-between"
                style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
            >
                <Brand />
                <button
                    type="button"
                    onClick={() => setMobileOpen(true)}
                    className="p-2 rounded-lg"
                    style={{ border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                    aria-label="Open navigation menu"
                >
                    <Menu size={16} />
                </button>
            </header>

            {mobileOpen && (
                <div className="fixed inset-0 z-40 md:hidden">
                    <button
                        type="button"
                        onClick={closeMobile}
                        className="absolute inset-0 bg-black/60"
                        aria-label="Close navigation menu"
                    />
                    <aside
                        className="absolute left-0 top-0 h-full w-72 max-w-[85vw] flex flex-col border-r"
                        style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
                    >
                        <div className="px-5 py-4 border-b flex items-center justify-between" style={{ borderColor: 'var(--border)' }}>
                            <Brand />
                            <button
                                type="button"
                                onClick={closeMobile}
                                className="p-2 rounded-lg"
                                style={{ border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                                aria-label="Close navigation drawer"
                            >
                                <X size={16} />
                            </button>
                        </div>
                        <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
                            <NavLinks pathname={pathname} onNavigate={closeMobile} />
                        </nav>
                        <div className="px-3 py-3 border-t" style={{ borderColor: 'var(--border)' }}>
                            <LogoutButton onLogout={handleLogout} />
                        </div>
                    </aside>
                </div>
            )}

            <aside
                className="hidden md:flex w-64 h-screen flex-col border-r sticky top-0"
                style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
            >
                <div className="px-5 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
                    <Brand />
                </div>

                <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
                    <NavLinks pathname={pathname} />
                </nav>

                <div className="px-3 py-3 border-t" style={{ borderColor: 'var(--border)' }}>
                    <LogoutButton onLogout={handleLogout} />
                </div>
            </aside>
        </>
    );
}
