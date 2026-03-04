'use client';
import DashboardLayout from '@/components/layout/DashboardLayout';
import { BookOpen } from 'lucide-react';
import Link from 'next/link';

export default function SavedPage() {
    return (
        <DashboardLayout>
            <div className="max-w-3xl mx-auto">
                <div className="flex items-center gap-3 mb-6">
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: 'rgba(99,102,241,0.2)' }}>
                        <BookOpen size={16} style={{ color: '#6366f1' }} />
                    </div>
                    <h1 className="text-xl font-bold text-white">Saved Analyses</h1>
                </div>
                <div className="card text-center py-12">
                    <BookOpen size={32} className="mx-auto mb-3" style={{ color: 'var(--text-muted)' }} />
                    <p className="text-sm text-white mb-1">Your deep analyses are saved in memory</p>
                    <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>
                        Use the Memory Search to recall and explore your past research sessions semantically.
                    </p>
                    <Link href="/memory" className="px-4 py-2 rounded-lg text-sm font-medium text-white inline-block" style={{ background: 'var(--accent)' }}>
                        Go to Memory Search →
                    </Link>
                </div>
            </div>
        </DashboardLayout>
    );
}
