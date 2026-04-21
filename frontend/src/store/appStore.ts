import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, SyncState, Page, Notification, DateRange } from '../types';

interface AppState {
  // Auth
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  logout: () => void;

  // Sync
  syncState: SyncState;
  setSyncState: (s: Partial<SyncState>) => void;

  // UI
  activePage: Page;
  setActivePage: (p: Page) => void;
  sidebarCollapsed: boolean;
  toggleSidebar: () => void;

  // Filters / Date Range
  globalDateRange: DateRange;
  setGlobalDateRange: (r: DateRange) => void;

  // Notifications
  notifications: Notification[];
  addNotification: (n: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;

  // Search
  lastSearchQuery: string;
  setLastSearchQuery: (q: string) => void;
  recentQueries: string[];
  addRecentQuery: (q: string) => void;
}

const defaultDateRange: DateRange = {
  from: new Date(Date.now() - 365 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
  to: new Date().toISOString().split('T')[0],
};

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      isAuthenticated: false,
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      logout: () =>
        set({
          user: null,
          isAuthenticated: false,
          syncState: { status: 'idle', emails_total: 0, emails_synced: 0, last_synced_at: null, phase: 'idle', backfill_complete: null, detail: null, oldest_synced_at: null },
          activePage: 'home',
        }),

      // Sync
      syncState: { status: 'idle', emails_total: 0, emails_synced: 0, last_synced_at: null, phase: 'idle', backfill_complete: null, detail: null, oldest_synced_at: null },
      setSyncState: (s) => set((prev) => ({ syncState: { ...prev.syncState, ...s } })),

      // UI
      activePage: 'home',
      setActivePage: (activePage) => set({ activePage }),
      sidebarCollapsed: false,
      toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),

      // Date range
      globalDateRange: defaultDateRange,
      setGlobalDateRange: (globalDateRange) => set({ globalDateRange }),

      // Notifications
      notifications: [],
      addNotification: (n) => {
        const id = Math.random().toString(36).slice(2);
        set((s) => ({ notifications: [...s.notifications, { ...n, id }] }));
        setTimeout(() => get().removeNotification(id), 4500);
      },
      removeNotification: (id) =>
        set((s) => ({ notifications: s.notifications.filter((n) => n.id !== id) })),

      // Search
      lastSearchQuery: '',
      setLastSearchQuery: (q) => set({ lastSearchQuery: q }),
      recentQueries: [],
      addRecentQuery: (q) =>
        set((s) => ({
          recentQueries: [q, ...s.recentQueries.filter((r) => r !== q)].slice(0, 8),
        })),
    }),
    {
      name: 'maillens-store',
      partialize: (s) => ({
        user: s.user,
        isAuthenticated: s.isAuthenticated,
        sidebarCollapsed: s.sidebarCollapsed,
        globalDateRange: s.globalDateRange,
        recentQueries: s.recentQueries,
      }),
    }
  )
);
