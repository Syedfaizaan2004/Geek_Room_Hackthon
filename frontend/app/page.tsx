'use client';
import DashboardLayout from '@/components/layout/DashboardLayout';
import Link from 'next/link';
import { Zap, Brain, GitCompare, ShieldAlert, TrendingUp, BarChart3, Activity } from 'lucide-react';

const quickLinks = [
  { href: '/quick', icon: Zap, label: 'Quick Analysis', desc: 'Fast snapshot in ~20s', color: '#3b82f6' },
  { href: '/deep', icon: Brain, label: 'Deep Research', desc: 'Full 8-engine analysis', color: '#8b5cf6' },
  { href: '/compare', icon: GitCompare, label: 'Peer Compare', desc: 'Benchmark competitors', color: '#10b981' },
  { href: '/risk', icon: ShieldAlert, label: 'Risk Overview', desc: 'Detect hidden risks', color: '#ef4444' },
  { href: '/scenario', icon: BarChart3, label: 'Scenario Test', desc: 'Stress-test assumptions', color: '#f59e0b' },
  { href: '/chat', icon: Activity, label: 'AI Chat', desc: 'Ask follow-up questions', color: '#06b6d4' },
];

const featured = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX'];

export default function Home() {
  return (
    <DashboardLayout>
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-xl sm:text-2xl font-bold text-white">Research Dashboard</h1>
          <p style={{ color: 'var(--text-muted)' }} className="text-sm mt-1">
            AI-powered financial analysis with real-time market data and LLM insights
          </p>
        </div>

        {/* Quick Action Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4 mb-8">
          {quickLinks.map(({ href, icon: Icon, label, desc, color }) => (
            <Link key={href} href={href}
              className="card hover:border-opacity-80 transition-all group p-5"
              style={{ borderColor: 'var(--border)' }}>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${color}20` }}>
                  <Icon size={18} style={{ color }} />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white group-hover:text-blue-400 transition-colors">{label}</p>
                  <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>{desc}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>

        {/* Featured Tickers */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} style={{ color: 'var(--accent)' }} />
            <h2 className="text-sm font-semibold text-white">Quick Access — Popular Tickers</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {featured.map((ticker) => (
              <Link key={ticker} href={`/quick?ticker=${ticker}`}
                className="px-4 py-2 rounded-lg text-sm font-medium transition-all hover:text-white"
                style={{ background: 'var(--bg-primary)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}>
                {ticker}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
