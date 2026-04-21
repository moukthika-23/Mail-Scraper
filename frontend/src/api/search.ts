import { apiClient } from './client';
import type { SearchRequest, SearchResponse } from '../types';

// ─── Real API ─────────────────────────────────────────────────────────────────
export async function searchEmails(req: SearchRequest): Promise<SearchResponse> {
  const res = await apiClient.post<SearchResponse>('/search', req);
  return res.data;
}
