import React from 'react';
import { BellIcon, ArrowPathIcon, UserIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useAppStore } from '../../store/appStore';
import { triggerSync, fetchSyncStatus } from '../../api/sync';
import './Topbar.css';

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  home:      { title: 'Home',           subtitle: 'AI-powered inbox intelligence' },
  search:    { title: 'Smart Search',   subtitle: 'Semantic + keyword search with LLM synthesis' },
  dashboard: { title: 'Analytics',      subtitle: 'Chart-driven inbox insights' },
  analyse:   { title: 'AI Analysis',    subtitle: 'Free-form query engine powered by Groq LLM' },
  settings:  { title: 'Settings',       subtitle: 'Manage sync, account, and preferences' },
};

const Topbar: React.FC = () => {
  const { activePage, user, setActivePage, syncState, setSyncState } = useAppStore();
  const { title, subtitle } = PAGE_TITLES[activePage] || PAGE_TITLES.home;

  const handleSync = async () => {
    setSyncState({ status: 'syncing', phase: 'incremental', emails_total: 0, emails_synced: 0, detail: 'Syncing latest mail…', backfill_complete: false });

    try {
      await triggerSync('incremental');
      const st = await fetchSyncStatus();
      setSyncState(st);
    } catch (e) {
      setSyncState({ status: 'error' });
    }
  };

  return (
    <header className="topbar" role="banner">
      {/* Page info */}
      <div className="topbar__page">
        <h1 className="topbar__title">{title}</h1>
        <p className="topbar__subtitle">{subtitle}</p>
      </div>

      {/* Quick search shortcut */}
      <button
        className="topbar__search-pill"
        id="topbar-search-shortcut"
        onClick={() => setActivePage('search')}
      >
        <MagnifyingGlassIcon width={14} />
        <span>Search your inbox…</span>
        <kbd className="topbar__kbd">⌘K</kbd>
      </button>

      {/* Actions */}
      <div className="topbar__actions">
        {/* Sync button */}
        <button
          className={`topbar__action-btn ${syncState.status === 'syncing' ? 'topbar__action-btn--syncing' : ''}`}
          id="topbar-sync-btn"
          onClick={handleSync}
          title="Sync Gmail"
          disabled={syncState.status === 'syncing'}
        >
          <ArrowPathIcon width={16} className={syncState.status === 'syncing' ? 'animate-spin' : ''} />
        </button>

        {/* Notifications */}
        <button className="topbar__action-btn" id="topbar-notifications" title="Notifications">
          <BellIcon width={16} />
          <span className="topbar__notif-dot" />
        </button>

        {/* Avatar */}
        <button className="topbar__avatar" id="topbar-avatar" onClick={() => setActivePage('settings')}>
          {user?.picture ? (
            <img src={user.picture} alt={user.name} />
          ) : (
            <UserIcon width={16} />
          )}
        </button>
      </div>
    </header>
  );
};

export default Topbar;
