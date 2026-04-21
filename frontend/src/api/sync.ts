import { apiClient } from './client';
import type { SyncState } from '../types';

export async function triggerSync(mode: 'full' | 'incremental' | 'smart', dateRange?: { date_from?: string; date_to?: string }): Promise<{ task_id: string, status: string }> {
  const payload: any = { mode };
  if (dateRange?.date_from) payload.date_from = dateRange.date_from;
  if (dateRange?.date_to) payload.date_to = dateRange.date_to;
  const res = await apiClient.post('/sync/start', payload);
  return res.data;
}

export async function fetchSyncStatus(): Promise<SyncState> {
  const res = await apiClient.get<SyncState>('/sync/status');
  return res.data;
}
