'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
    LayoutDashboard, Zap, Brain, GitCompare, ShieldAlert,
    BarChart3, Star, BookOpen, User, MessageSquare, Database, LogOut
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { useRouter } from 'next/navigation';

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

export default function Sidebar() {
    const pathname = usePathname();
    const { logout } = useAuthStore();
    const router = useRouter();

    const handleLogout = () => {
        logout();
        router.push('/login');
    };

    return (
        <aside className="w-64 h-screen flex flex-col border-r sticky top-0" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
            <div className="px-5 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
                <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'var(--accent)' }}>
                        <Brain size={16} className="text-white" />
                    </div>
                    <div>
                        <p className="text-sm font-bold text-white">FinAgent</p>
                        <p className="text-xs" style={{ color: 'var(--text-muted)' }}>AI Research Platform</p>
                    </div>
                </div>
            </div>

            <nav className="flex-1 px-3 py-4 overflow-y-auto space-y-0.5">
                {navItems.map(({ href, icon: Icon, label }) => {
                    const isActive = pathname === href;
                    return (
                        <Link key={href} href={href}
                            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all"
                            style={isActive
                                ? { background: 'rgba(59,130,246,0.15)', color: '#60a5fa', borderLeft: '3px solid #3b82f6' }
                                : { color: 'var(--text-muted)' }
                            }
                        >
                            <Icon size={16} />
                            <span>{label}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className="px-3 py-3 border-t" style={{ borderColor: 'var(--border)' }}>
                <button onClick={handleLogout}
                    className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all hover:bg-red-500/10"
                    style={{ color: 'var(--text-muted)' }}>
                    <LogOut size={16} />
                    <span>Logout</span>
                </button>
            </div>
        </aside>
    );
}
