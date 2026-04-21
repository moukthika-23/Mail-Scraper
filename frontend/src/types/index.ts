// ─── Auth & User ────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
  google_id: string;
  created_at: string;
}

export interface SyncState {
  status: 'idle' | 'syncing' | 'done' | 'error';
  emails_total: number;
  emails_synced: number;
  last_synced_at: string | null;
  history_id?: string;
  phase?: 'idle' | 'recent' | 'backfill' | 'incremental' | 'complete' | 'error' | string;
  detail?: string | null;
  oldest_synced_at?: string | null;
  backfill_complete?: boolean | null;
  backfill_cursor_end?: string | null;
}

// ─── Email ───────────────────────────────────────────────────────────────────
export interface Email {
  id: string;
  gmail_id: string;
  thread_id: string;
  subject: string;
  sender_email: string;
  sender_name: string;
  body_text: string;
  snippet: string;
  date: string;
  is_read: boolean;
  is_starred: boolean;
  labels: string[];
  raw_size_bytes: number;
}

export interface EmailCard {
  id: string;
  subject: string;
  sender_email: string;
  sender_name: string;
  snippet: string;
  date: string;
  labels: string[];
  relevance_score?: number;
}

// ─── Search ──────────────────────────────────────────────────────────────────
export interface SearchRequest {
  query: string;
  filters?: {
    labels?: string[];
    senders?: string[];
    date_from?: string;
    date_to?: string;
  };
  top_k?: number;
}

export interface SearchResponse {
  answer: string;
  sources: EmailCard[];
  query_time_ms: number;
}

// ─── Analytics ───────────────────────────────────────────────────────────────
export interface LabelFrequency {
  label: string;
  count: number;
  percentage: number;
}

export interface VolumeDataPoint {
  date: string;
  count: number;
}

export interface SenderStat {
  sender_email: string;
  sender_name: string;
  domain: string;
  count: number;
  first_seen: string;
  last_seen: string;
}

export interface HeatmapCell {
  hour: number;
  day: number; // 0=Mon … 6=Sun
  count: number;
}

export interface ThreadDepthBin {
  depth: string;
  count: number;
}

export interface AnalyticsSummary {
  total_emails: number;
  total_senders: number;
  total_labels: number;
  total_threads: number;
  avg_emails_per_day: number;
  busiest_day: string;
  busiest_hour: number;
  top_label: string;
  top_sender: string;
  unread_count: number;
  starred_count: number;
}

// ─── Custom Analysis ─────────────────────────────────────────────────────────
export type ChartType = 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap' | 'table';

export interface ChartSpec {
  type: ChartType;
  title: string;
  x_label?: string;
  y_label?: string;
  data: Record<string, unknown>[];
  color_scheme?: string[];
}

export interface CustomQueryResponse {
  query_text: string;
  chart_spec: ChartSpec;
  explanation: string;
  query_time_ms: number;
}

export interface SavedQuery {
  id: string;
  name: string;
  query_text: string;
  chart_spec_json: ChartSpec;
  created_at: string;
}

// ─── Filter ──────────────────────────────────────────────────────────────────
export interface DateRange {
  from: string;
  to: string;
}

export type Granularity = 'day' | 'week' | 'month';

// ─── UI State ────────────────────────────────────────────────────────────────
export type Page = 'home' | 'search' | 'dashboard' | 'analyse' | 'settings';

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message?: string;
}
