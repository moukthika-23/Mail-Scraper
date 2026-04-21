import React from 'react';
import { MagnifyingGlassIcon, Squares2X2Icon, BeakerIcon, ArrowTrendingUpIcon, EnvelopeIcon, BoltIcon, ArrowRightIcon, StarIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '../store/appStore';
import { useQuery } from '@tanstack/react-query';
import { fetchSummary } from '../api/analytics';
import { fetchSyncStatus, triggerSync } from '../api/sync';
import './HomePage.css';

const QUICK_ACTIONS = [
  { id: 'go-search',    icon: <MagnifyingGlassIcon width={20} />,         label: 'Smart Search',    desc: 'Ask anything about your inbox',   page: 'search'    as const, color: 'purple' },
  { id: 'go-dashboard', icon: <Squares2X2Icon width={20} />, label: 'Analytics',       desc: 'Charts · Heatmaps · Trends',      page: 'dashboard' as const, color: 'blue'   },
  { id: 'go-analyse',   icon: <BeakerIcon width={20} />,          label: 'AI Analysis',     desc: 'Free-form custom queries',        page: 'analyse'   as const, color: 'green'  },
];

const HomePage: React.FC = () => {
  const { setActivePage, user, isAuthenticated, syncState, setSyncState, globalDateRange } = useAppStore();
  const { data: summary } = useQuery({ queryKey: ['summary'], queryFn: fetchSummary, staleTime: 5 * 60 * 1000 });

  const formatNum = (n?: number) => {
    if (n === undefined) return '—';
    return n >= 1000 ? `${(n / 1000).toFixed(1)}k` : n.toString();
  };

  const recentInsights = summary ? [
    {
      icon: <ArrowTrendingUpIcon width={14} />,
      text: `${formatNum(summary.total_emails)} emails indexed across ${formatNum(summary.total_senders)} senders`,
      color: 'green',
    },
    {
      icon: <EnvelopeIcon width={14} />,
      text: `${formatNum(summary.unread_count)} unread emails waiting`,
      color: 'amber',
    },
    {
      icon: <BoltIcon width={14} />,
      text: `${summary.top_sender !== 'N/A' ? summary.top_sender : 'No sender data yet'} is your top sender`,
      color: 'purple',
    },
    {
      icon: <StarIcon width={14} />,
      text: `${formatNum(summary.starred_count)} starred emails worth revisiting`,
      color: 'blue',
    },
  ] : [];

  const handleSmartSync = async () => {
    setSyncState({ status: 'syncing', phase: 'recent', emails_total: 0, emails_synced: 0, detail: 'Syncing recent mail…', backfill_complete: false });
    setActivePage('settings');

    try {
      await triggerSync('smart', { date_from: globalDateRange.from, date_to: globalDateRange.to });
      const st = await fetchSyncStatus();
      setSyncState(st);
    } catch {
      setSyncState({ status: 'error' });
    }
  };

  return (
    <div className="home animate-fade-in">
      {/* Hero */}
      <div className="home__hero">
        <div>
          <h2 className="home__hero-title">
            Good {getGreeting()}, <span>{user?.name?.split(' ')[0] ?? 'there'}</span>
          </h2>
          <p className="home__hero-sub">
            Your inbox at a glance — {formatNum(summary?.total_emails)} emails indexed, AI-powered insights ready.
          </p>
        </div>
        <div className="home__hero-stats">
          <div className="home__hero-stat" id="hero-stat-emails">
            <span className="home__hero-stat-value">{formatNum(summary?.total_emails)}</span>
            <span className="home__hero-stat-label">Emails</span>
          </div>
          <div className="home__hero-stat-divider" />
          <div className="home__hero-stat" id="hero-stat-senders">
            <span className="home__hero-stat-value">{formatNum(summary?.total_senders)}</span>
            <span className="home__hero-stat-label">Senders</span>
          </div>
          <div className="home__hero-stat-divider" />
          <div className="home__hero-stat" id="hero-stat-unread">
            <span className="home__hero-stat-value">{formatNum(summary?.unread_count)}</span>
            <span className="home__hero-stat-label">Unread</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="home__section">
        <h3 className="home__section-title">Quick Actions</h3>
        <div className="home__actions-grid">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a.id}
              id={a.id}
              className="home__action-card"
              onClick={() => setActivePage(a.page)}
            >
              <div className="home__action-icon">{a.icon}</div>
              <div className="home__action-body">
                <div className="home__action-label">{a.label}</div>
                <div className="home__action-desc">{a.desc}</div>
              </div>
              <ArrowRightIcon width={16} className="home__action-arrow" />
            </button>
          ))}
        </div>
      </div>

      {/* Insights strip */}
      <div className="home__section">
        <h3 className="home__section-title">Latest Insights</h3>
        <div className="home__insights">
          {recentInsights.length > 0 ? (
            recentInsights.map((ins, i) => (
              <div key={i} className="home__insight animate-fade-in" style={{ animationDelay: `${i * 80}ms` }}>
                <span className="home__insight-icon">{ins.icon}</span>
                <span>{ins.text}</span>
              </div>
            ))
          ) : (
            <div className="home__insight animate-fade-in">
              <span className="home__insight-icon"><ArrowTrendingUpIcon width={14} /></span>
              <span>Loading live inbox insights from your mailbox...</span>
            </div>
          )}
        </div>
      </div>

      {/* Sync CTA */}
      {!isAuthenticated && (
        <div className="home__sync-cta glass-card" id="home-sync-cta">
          <div className="home__sync-cta-left">
            <div className="home__sync-cta-icon">
              <EnvelopeIcon width={22} />
            </div>
            <div>
              <div className="home__sync-cta-title">Connect your Gmail</div>
              <div className="home__sync-cta-sub">Authenticate with Google to start ingesting your inbox. Read-only access — your data stays private.</div>
            </div>
          </div>
          <button className="home__sync-cta-btn" id="home-connect-gmail-btn" onClick={() => setActivePage('settings')}>
            Connect Gmail <ArrowRightIcon width={15} />
          </button>
        </div>
      )}

      {isAuthenticated && syncState.status !== 'syncing' && syncState.emails_total === 0 && (
        <div className="home__sync-cta glass-card" id="home-sync-cta" style={{ background: 'rgba(56, 189, 248, 0.1)', borderColor: 'rgba(56, 189, 248, 0.2)' }}>
          <div className="home__sync-cta-left">
            <div className="home__sync-cta-icon">
              <BoltIcon width={22} style={{ color: '#38bdf8' }} />
            </div>
            <div>
              <div className="home__sync-cta-title">Start Smart Sync</div>
              <div className="home__sync-cta-sub">Instantly sync your last 30 days of emails and view them while older mail gently backfills in the background.</div>
            </div>
          </div>
          <button 
            className="home__sync-cta-btn" 
            id="home-start-sync-btn" 
            style={{ background: '#38bdf8', color: '#0f172a' }} 
            onClick={handleSmartSync}
          >
            Smart Sync <ArrowRightIcon width={15} />
          </button>
        </div>
      )}
    </div>
  );
};

function getGreeting() {
  const h = new Date().getHours();
  if (h < 12) return 'morning';
  if (h < 17) return 'afternoon';
  return 'evening';
}

export default HomePage;
