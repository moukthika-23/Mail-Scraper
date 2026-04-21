import { apiClient } from './client';
import type { CustomQueryResponse, SavedQuery } from '../types';

export async function runCustomQuery(query: string): Promise<CustomQueryResponse> {
  const res = await apiClient.post<CustomQueryResponse>('/analyse/custom', { query });
  return res.data;
}

export async function fetchSavedQueries(): Promise<SavedQuery[]> {
  const res = await apiClient.get<SavedQuery[]>('/queries');
  return res.data;
}

export async function saveQuery(name: string, query_text: string, chart_spec_json: object): Promise<SavedQuery> {
  const res = await apiClient.post<SavedQuery>('/queries', { name, query_text, chart_spec_json });
  return res.data;
}

export async function startSync(mode: 'full' | 'incremental' = 'incremental'): Promise<void> {
  await apiClient.post('/sync/start', { mode });
}
