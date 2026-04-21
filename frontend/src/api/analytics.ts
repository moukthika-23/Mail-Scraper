import { apiClient } from './client';
import type {
  AnalyticsSummary,
  LabelFrequency,
  VolumeDataPoint,
  SenderStat,
  HeatmapCell,
  ThreadDepthBin,
  Granularity,
} from '../types';

// ─── API functions ────────────────────────────────────────────────────────────
export async function fetchSummary(): Promise<AnalyticsSummary> {
  const res = await apiClient.get<AnalyticsSummary>('/analytics/summary');
  return res.data;
}

export async function fetchLabelFrequency(from: string, to: string): Promise<LabelFrequency[]> {
  const res = await apiClient.get<LabelFrequency[]>('/analytics/labels', { params: { date_from: from, date_to: to } });
  return res.data;
}

export async function fetchVolume(from: string, to: string, granularity: Granularity = 'day'): Promise<VolumeDataPoint[]> {
  const res = await apiClient.get<VolumeDataPoint[]>('/analytics/volume', { params: { date_from: from, date_to: to, granularity } });
  return res.data;
}

export async function fetchTopSenders(limit = 10): Promise<SenderStat[]> {
  const res = await apiClient.get<SenderStat[]>('/analytics/senders', { params: { limit } });
  return res.data;
}

export async function fetchHeatmap(from: string, to: string): Promise<HeatmapCell[]> {
  const res = await apiClient.get<HeatmapCell[]>('/analytics/heatmap', { params: { date_from: from, date_to: to } });
  return res.data;
}

export async function fetchThreadDepth(from: string, to: string): Promise<ThreadDepthBin[]> {
  const res = await apiClient.get<ThreadDepthBin[]>('/analytics/threads', { params: { date_from: from, date_to: to } });
  return res.data;
}
