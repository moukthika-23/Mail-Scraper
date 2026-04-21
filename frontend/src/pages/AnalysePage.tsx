import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { runCustomQuery, fetchSavedQueries, saveQuery } from '../api/analyse';
import type { CustomQueryResponse, ChartSpec } from '../types';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { SparklesIcon, PaperAirplaneIcon, BookmarkIcon, ClockIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import './AnalysePage.css';

const PALETTE = ['#7c5cfc','#4f9cf9','#22d3ee','#34d399','#fbbf24','#f43f5e','#fb923c'];

const EXAMPLE_QUERIES = [
  'Show me email volume by sender domain for the last 30 days',
  'Which labels have the most unread emails?',
  'What hour of the day do I send the most emails?',
  'Show a week-by-week trend of inbox volume this year',
  'Which senders have the longest reply latency?',
  'How many emails contain attachments vs plain text?',
];

function ChartRenderer({ spec }: { spec: ChartSpec }) {
  const { type, data, x_label, y_label } = spec;
  const xKey = x_label ?? Object.keys(data[0])[0];
  const yKey = y_label ?? Object.keys(data[0])[1];

  if (type === 'pie') {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <PieChart>
          <Pie data={data} dataKey={yKey} nameKey={xKey} cx="50%" cy="50%" outerRadius={110} paddingAngle={2} label={({ name, value }: any) => `${name || 'Unknown'}: ${value}`}>
            {data.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
          </Pie>
          <Tooltip
            contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border-medium)', borderRadius:10 }}
            itemStyle={{ color:'var(--text-primary)' }}
          />
        </PieChart>
      </ResponsiveContainer>
    );
  }
  if (type === 'line') {
    return (
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#dee2e6" />
          <XAxis dataKey={xKey} tick={{ fontSize:10, fill:'var(--text-muted)' }} />
          <YAxis tick={{ fontSize:10, fill:'var(--text-muted)' }} />
          <Tooltip contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border-medium)', borderRadius:10 }} itemStyle={{ color:'var(--text-primary)' }} />
          <Line type="monotone" dataKey={yKey} stroke="#7c5cfc" strokeWidth={2.5} dot={{ r:3, fill:'#7c5cfc' }} />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  // default: bar
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#dee2e6" />
        <XAxis dataKey={xKey} tick={{ fontSize:10, fill:'var(--text-muted)' }} />
        <YAxis tick={{ fontSize:10, fill:'var(--text-muted)' }} />
        <Tooltip contentStyle={{ background:'var(--bg-card)', border:'1px solid var(--border-medium)', borderRadius:10 }} itemStyle={{ color:'var(--text-primary)' }} />
        <Bar dataKey={yKey} name="Count" radius={[4,4,0,0]}>
          {data.map((_,i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

const AnalysePage: React.FC = () => {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<CustomQueryResponse | null>(null);
  const [saveName, setSaveName] = useState('');
  const [showSave, setShowSave] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: saved = [] } = useQuery({ queryKey: ['savedQueries'], queryFn: fetchSavedQueries });

  const { mutate: submit, isPending } = useMutation({
    mutationFn: (q: string) => runCustomQuery(q),
    onSuccess: (data) => {
      setError(null);
      setResult(data);
      setSaveName(data.chart_spec.title);
    },
    onError: (err) => {
      setResult(null);
      setShowSave(false);
      const detail = axios.isAxiosError(err)
        ? ((err.response?.data as { detail?: string } | undefined)?.detail ?? err.message)
        : err instanceof Error
          ? err.message
          : 'Live analysis failed. Please check the backend configuration and try again.';
      setError(detail);
    },
  });

  const { mutate: doSave, isPending: saving } = useMutation({
    mutationFn: () => saveQuery(saveName, result!.query_text, result!.chart_spec),
    onSuccess: () => setShowSave(false),
  });

  const handleSubmit = (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    setError(null);
    setResult(null);
    submit(trimmed);
  };

  return (
    <div className="analyse-page animate-fade-in">
      {/* Left panel */}
      <div className="analyse-page__left">
        {/* Query input */}
        <div className="analyse-page__query-card">
          <div className="analyse-page__query-header">
            <SparklesIcon width={18} className="analyse-page__query-icon" />
            <h2 className="analyse-page__query-title">Custom Analysis</h2>
          </div>
          <p className="analyse-page__query-desc">
            Ask any question about your inbox. The AI will query your data and generate an interactive chart with an explanation.
          </p>
          <textarea
            id="analyse-query-input"
            className="analyse-page__textarea"
            placeholder="e.g. Show me email volume by sender domain for the last 30 days…"
            value={query}
            rows={4}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit(query); }}
          />
          <div className="analyse-page__query-footer">
            <span className="analyse-page__hint">⌘↵ to submit</span>
            <button
              id="analyse-submit-btn"
              className={`analyse-page__submit ${isPending ? 'analyse-page__submit--loading' : ''}`}
              onClick={() => handleSubmit(query)}
              disabled={isPending || !query.trim()}
            >
              {isPending ? 'Generating…' : <><PaperAirplaneIcon width={14} /> Analyse</>}
            </button>
          </div>
        </div>

        {/* Example queries */}
        <div className="analyse-page__examples">
          <div className="analyse-page__examples-label">Example queries</div>
          {EXAMPLE_QUERIES.map((q) => (
            <button key={q} className="analyse-page__example-item" onClick={() => setQuery(q)}>
              <ChartBarIcon width={13} /> {q}
            </button>
          ))}
        </div>

        {/* Saved queries */}
        {saved.length > 0 && (
          <div className="analyse-page__saved">
            <div className="analyse-page__examples-label">Saved queries</div>
            {saved.map((sq) => (
              <button
                key={sq.id}
                className="analyse-page__example-item"
                onClick={() => { setQuery(sq.query_text); handleSubmit(sq.query_text); }}
              >
                <ClockIcon width={13} /> {sq.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Right panel — output */}
      <div className="analyse-page__right">
        {error && !isPending && (
          <div
            style={{
              marginBottom: 16,
              padding: '12px 14px',
              borderRadius: 12,
              border: '1px solid rgba(244, 63, 94, 0.28)',
              background: 'rgba(244, 63, 94, 0.08)',
              color: 'var(--text-primary)',
            }}
          >
            <strong>Live analysis failed.</strong> {error}
          </div>
        )}

        {!result && !isPending && (
          <div className="analyse-page__empty">
            <div className="analyse-page__empty-icon animate-float">
              <SparklesIcon width={36} />
            </div>
            <h3>Ask a question to generate a chart</h3>
            <p>The AI will interpret your query, run analysis on your inbox data, and render an interactive visualization with a natural language explanation.</p>
          </div>
        )}

        {isPending && (
          <div className="analyse-page__loading">
            <div className="analyse-page__loading-bar">
              <div className="analyse-page__loading-fill" />
            </div>
            <div className="skeleton" style={{ height: 280, borderRadius: 12, marginTop: 24 }} />
            <div style={{ marginTop: 16, display:'flex', flexDirection:'column', gap:8 }}>
              <div className="skeleton" style={{ height: 12, width: '60%' }} />
              <div className="skeleton" style={{ height: 12, width: '85%' }} />
              <div className="skeleton" style={{ height: 12, width: '45%' }} />
            </div>
          </div>
        )}

        {result && !isPending && (
          <div className="analyse-page__result animate-fade-in">
            {/* Chart card */}
            <div className="analyse-page__chart-card">
              <div className="analyse-page__chart-header">
                <div>
                  <h3 className="analyse-page__chart-title">{result.chart_spec.title}</h3>
                  <span className="badge badge-purple" style={{ marginTop: 4 }}>{result.chart_spec.type} chart</span>
                </div>
                <div className="analyse-page__chart-actions">
                  <span className="analyse-page__qtime">{result.query_time_ms}ms</span>
                  <button className="analyse-page__save-btn" id="analyse-save-btn" onClick={() => setShowSave(true)}>
                    <BookmarkIcon width={14} /> Save
                  </button>
                </div>
              </div>
              <ChartRenderer spec={result.chart_spec} />
            </div>

            {/* Explanation */}
            <div className="analyse-page__explanation">
              <div className="analyse-page__explanation-label">
                <SparklesIcon width={14} /> AI Explanation
              </div>
              <p>{result.explanation}</p>
            </div>

            {/* Save modal */}
            {showSave && (
              <div className="analyse-page__save-modal animate-fade-in">
                <h4>Save Query</h4>
                <input
                  className="analyse-page__save-input"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  placeholder="Query name…"
                />
                <div className="analyse-page__save-actions">
                  <button className="analyse-page__save-cancel" onClick={() => setShowSave(false)}>Cancel</button>
                  <button className="analyse-page__save-confirm" onClick={() => doSave()} disabled={saving}>
                    {saving ? 'Saving…' : 'Save'}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysePage;
