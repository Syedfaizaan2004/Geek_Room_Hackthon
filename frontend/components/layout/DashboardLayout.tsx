'use client';
import { ReactNode, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Sidebar from './Sidebar';
import { useAuthStore } from '@/store/authStore';

export default function DashboardLayout({ children }: { children: ReactNode }) {
    const { isAuthenticated, hydrated, hydrate } = useAuthStore();
    const router = useRouter();

    useEffect(() => {
        hydrate();
    }, [hydrate]);

    useEffect(() => {
        if (hydrated && !isAuthenticated) {
            router.replace('/login');
        }
    }, [hydrated, isAuthenticated, router]);

    if (!hydrated) {
        return <div className="h-screen" style={{ background: 'var(--bg-primary)' }} />;
    }

    if (!isAuthenticated) return null;

    return (
        <div className="h-screen overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
            <div className="flex h-full flex-col md:flex-row">
                <Sidebar />
                <main className="flex-1 overflow-y-auto p-4 sm:p-5 md:p-6">
                    {children}
                </main>
            </div>
        </div>
    );
}
