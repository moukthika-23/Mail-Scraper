import React, { useEffect } from 'react';
import { useAppStore } from '../store/appStore';
import { ShieldCheckIcon, ArrowPathIcon, ArrowLeftOnRectangleIcon, MoonIcon, CircleStackIcon, KeyIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { triggerSync, fetchSyncStatus } from '../api/sync';
import { AUTH_GOOGLE_URL } from '../api/client';
import './SettingsPage.css';

const SettingsPage: React.FC = () => {
  const { user, logout, globalDateRange, setGlobalDateRange, syncState, setSyncState, isAuthenticated } = useAppStore();
  const isBackfillPending = syncState.backfill_complete === false;

  useEffect(() => {
    if (!isAuthenticated) return;

    fetchSyncStatus()
      .then((st) => setSyncState(st))
      .catch(() => setSyncState({ status: 'error' }));
  }, [isAuthenticated, setSyncState]);

  const handleFullSync = async () => {
    const detail = isBackfillPending ? 'Loading older data…' : 'Syncing recent mail…';
    setSyncState({ status: 'syncing', phase: isBackfillPending ? 'backfill' : 'recent', emails_total: 0, emails_synced: 0, detail, backfill_complete: false });

    try {
      await triggerSync('smart', { date_from: globalDateRange.from, date_to: globalDateRange.to });
      const st = await fetchSyncStatus();
      setSyncState(st);
    } catch (e) {
      setSyncState({ status: 'error' });
    }
  };

  return (
    <div className="settings animate-fade-in">
      {/* Profile */}
      <div className="settings__section">
        <h3 className="settings__section-title">Account</h3>
        <div className="settings__card">
          <div className="settings__profile">
            <div className="settings__avatar">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} />
              ) : (
                <span>{(user?.name ?? 'U').charAt(0)}</span>
              )}
            </div>
            <div>
              <div className="settings__profile-name">{user?.name ?? 'Not connected'}</div>
              <div className="settings__profile-email">{user?.email ?? 'Connect Gmail to get started'}</div>
            </div>
            <button 
              className={`settings__btn ${isAuthenticated ? 'bg-gray-800 text-gray-400 cursor-default' : 'settings__btn--ghost'}`} 
              id="settings-connect-btn" 
              onClick={() => {
                if (!isAuthenticated) {
                  window.location.href = AUTH_GOOGLE_URL;
                }
              }}
              disabled={isAuthenticated}
            >
              {isAuthenticated ? 'Connected' : <>Connect Gmail <ChevronRightIcon width={14} /></>}
            </button>
          </div>
        </div>
      </div>

      {/* Sync */}
      <div className="settings__section">
        <h3 className="settings__section-title">Gmail Sync</h3>
        <div className="settings__card">
          <div className="settings__row">
            <div className="settings__row-left">
              <div className="settings__row-icon">
                <ArrowPathIcon width={16} />
              </div>
              <div>
                <div className="settings__row-title">Sync Date Range</div>
                <div className="settings__row-sub">Only emails within this range will be indexed</div>
              </div>
            </div>
            <div className="settings__date-range">
              <input
                type="date"
                className="settings__date-input"
                value={globalDateRange.from}
                onChange={(e) => setGlobalDateRange({ ...globalDateRange, from: e.target.value })}
                id="settings-date-from"
              />
              <span style={{ color: 'var(--text-muted)', fontSize: 12 }}>to</span>
              <input
                type="date"
                className="settings__date-input"
                value={globalDateRange.to}
                onChange={(e) => setGlobalDateRange({ ...globalDateRange, to: e.target.value })}
                id="settings-date-to"
              />
            </div>
          </div>
          <div className="settings__divider" />
          <div className="settings__row">
            <div className="settings__row-left">
              <div className="settings__row-icon">
                <CircleStackIcon width={16} />
              </div>
              <div>
                <div className="settings__row-title">Smart Sync</div>
                <div className="settings__row-sub">Prioritize latest 30 days instantly, then backfill safely in the background</div>
              </div>
            </div>
            <button 
              className={`settings__btn settings__btn--primary ${syncState.status === 'syncing' ? 'opacity-50 cursor-not-allowed' : ''}`} 
              id="settings-full-sync-btn" 
              onClick={handleFullSync}
              disabled={syncState.status === 'syncing'}
            >
              {syncState.status === 'syncing' ? 'Syncing...' : isBackfillPending ? 'Load Older Data' : 'Start Smart Sync'}
            </button>
          </div>
        </div>
      </div>

      {/* Security */}
      <div className="settings__section">
        <h3 className="settings__section-title">Privacy & Security</h3>
        <div className="settings__card">
          <div className="settings__row">
            <div className="settings__row-left">
              <div className="settings__row-icon">
                <ShieldCheckIcon width={16} />
              </div>
              <div>
                <div className="settings__row-title">OAuth Scope</div>
                <div className="settings__row-sub">Read-only Gmail access — MailLens cannot send or modify emails</div>
              </div>
            </div>
            <span className="badge badge-green">Read Only</span>
          </div>
          <div className="settings__divider" />
          <div className="settings__row">
            <div className="settings__row-left">
              <div className="settings__row-icon">
                <KeyIcon width={16} />
              </div>
              <div>
                <div className="settings__row-title">Token Encryption</div>
                <div className="settings__row-sub">OAuth refresh tokens are encrypted at rest with AES-256</div>
              </div>
            </div>
            <span className="badge badge-green">AES-256</span>
          </div>
        </div>
      </div>

      {/* Appearance */}
      <div className="settings__section">
        <h3 className="settings__section-title">Appearance</h3>
        <div className="settings__card">
          <div className="settings__row">
            <div className="settings__row-left">
              <div className="settings__row-icon">
                <MoonIcon width={16} />
              </div>
              <div>
                <div className="settings__row-title">Theme</div>
                <div className="settings__row-sub">Currently using Dark Mode</div>
              </div>
            </div>
            <div className="settings__toggle-group">
              <button className="settings__toggle-btn settings__toggle-btn--active" id="settings-theme-dark">Dark</button>
              <button className="settings__toggle-btn" id="settings-theme-light">Light</button>
            </div>
          </div>
        </div>
      </div>

      {/* Danger zone */}
      <div className="settings__section">
        <h3 className="settings__section-title">Session</h3>
        <div className="settings__card">
          <div className="settings__row">
            <div className="settings__row-left">
              <div className="settings__row-icon">
                <ArrowLeftOnRectangleIcon width={16} />
              </div>
              <div>
                <div className="settings__row-title">Sign Out</div>
                <div className="settings__row-sub">Clears this browser session and returns to the Gmail sign-in screen</div>
              </div>
            </div>
            <button className="settings__btn settings__btn--danger" id="settings-signout-btn" onClick={logout}>
              Sign Out
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;
