import React from 'react';
import { HomeIcon, MagnifyingGlassIcon, Squares2X2Icon, BeakerIcon, Cog6ToothIcon, ChevronLeftIcon, ChevronRightIcon, EnvelopeIcon, BoltIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '../../store/appStore';
import type { Page } from '../../types';
import './Sidebar.css';

const NAV_ITEMS: { id: Page; icon: React.ReactNode; label: string; badge?: string }[] = [
  { id: 'home',      icon: <HomeIcon width={18} />,          label: 'Home' },
  { id: 'search',    icon: <MagnifyingGlassIcon width={18} />,        label: 'Smart Search' },
  { id: 'dashboard', icon: <Squares2X2Icon width={18} />, label: 'Analytics' },
  { id: 'analyse',   icon: <BeakerIcon width={18} />,        label: 'AI Analysis' },
  { id: 'settings',  icon: <Cog6ToothIcon width={18} />,      label: 'Settings' },
];

const Sidebar: React.FC = () => {
  const { activePage, setActivePage, sidebarCollapsed, toggleSidebar, syncState } = useAppStore();
  const syncStatusText =
    syncState.status === 'syncing'
      ? syncState.detail || `Syncing… ${syncState.emails_synced}/${syncState.emails_total}`
      : syncState.status === 'error'
        ? 'Sync failed'
        : syncState.last_synced_at
          ? syncState.backfill_complete === false
            ? 'Recent mail synced'
            : 'Up to date'
          : 'Not synced';

  return (
    <aside className={`sidebar ${sidebarCollapsed ? 'sidebar--collapsed' : ''}`}>
      {/* Logo */}
      <div className="sidebar__logo">
        <div className="sidebar__logo-icon">
          <EnvelopeIcon width={20} />
        </div>
        {!sidebarCollapsed && (
          <div className="sidebar__logo-text">
            <span className="sidebar__logo-name">MailLens</span>
            <span className="sidebar__logo-tag">AI Platform</span>
          </div>
        )}
      </div>

      <div className="sidebar__divider" />

      {/* Sync Status */}
      {!sidebarCollapsed && (
        <div className="sidebar__sync-status">
          <div className={`sidebar__sync-dot ${syncState.status === 'syncing' ? 'sidebar__sync-dot--active' : ''}`} />
          <span className="sidebar__sync-text">{syncStatusText}</span>
        </div>
      )}

      {/* Navigation */}
      <nav className="sidebar__nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            id={`nav-${item.id}`}
            className={`sidebar__nav-item ${activePage === item.id ? 'sidebar__nav-item--active' : ''}`}
            onClick={() => setActivePage(item.id)}
            title={sidebarCollapsed ? item.label : undefined}
          >
            <span className="sidebar__nav-icon">{item.icon}</span>
            {!sidebarCollapsed && <span className="sidebar__nav-label">{item.label}</span>}
            {!sidebarCollapsed && item.badge && (
              <span className="sidebar__nav-badge">{item.badge}</span>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom stats */}
      {!sidebarCollapsed && (
        <div className="sidebar__stats">
          <div className="sidebar__stat">
            <BoltIcon width={12} className="sidebar__stat-icon" />
            <span>Groq LLM Active</span>
          </div>
          <div className="sidebar__stat">
            <ArrowTrendingUpIcon width={12} className="sidebar__stat-icon" />
            <span>Free tier</span>
          </div>
        </div>
      )}

      {/* Collapse toggle */}
      <button className="sidebar__toggle" onClick={toggleSidebar} id="sidebar-toggle">
        {sidebarCollapsed ? <ChevronRightIcon width={16} /> : <ChevronLeftIcon width={16} />}
      </button>
    </aside>
  );
};

export default Sidebar;
