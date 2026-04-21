import React from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
} from 'recharts';
import { useAppStore } from '../store/appStore';
import {
  fetchSummary, fetchLabelFrequency, fetchVolume,
  fetchTopSenders, fetchHeatmap, fetchThreadDepth,
} from '../api/analytics';
import StatCard from '../components/Common/StatCard';
import { EnvelopeIcon, UsersIcon, TagIcon, ChatBubbleBottomCenterTextIcon, ArrowTrendingUpIcon, ClockIcon, StarIcon, EyeIcon, ChartBarIcon, ChartBarSquareIcon } from '@heroicons/react/24/outline';
import './DashboardPage.css';

const PALETTE = ['#7c5cfc', '#4f9cf9', '#22d3ee', '#34d399', '#fbbf24', '#f43f5e', '#fb923c'];
const DAYS = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => `${i}:00`);

const CustomTooltip = ({ active, payload, label }: Record<string, unknown>) => {
  if (active && Array.isArray(payload) && payload.length) {
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip__label">{String(label)}</p>
        {(payload as {name: string; value: unknown}[]).map((p) => (
          <p key={p.name} className="chart-tooltip__value">{p.name}: <strong>{String(p.value)}</strong></p>
        ))}
      </div>
    );
  }
  return null;
};

const DashboardPage: React.FC = () => {
  const { globalDateRange } = useAppStore();
  const { from, to } = globalDateRange;

  const { data: summary, isLoading: loadingSummary } = useQuery({
    queryKey: ['summary'],
    queryFn: fetchSummary,
    staleTime: 5 * 60 * 1000,
  });

  const { data: labels = [] } = useQuery({
    queryKey: ['labels', from, to],
    queryFn: () => fetchLabelFrequency(from, to),
    staleTime: 5 * 60 * 1000,
  });

  const { data: volume = [] } = useQuery({
    queryKey: ['volume', from, to],
    queryFn: () => fetchVolume(from, to, 'day'),
    staleTime: 5 * 60 * 1000,
  });

  const { data: senders = [] } = useQuery({
    queryKey: ['senders'],
    queryFn: () => fetchTopSenders(7),
    staleTime: 5 * 60 * 1000,
  });

  const { data: heatmapData = [] } = useQuery({
    queryKey: ['heatmap', from, to],
    queryFn: () => fetchHeatmap(from, to),
    staleTime: 5 * 60 * 1000,
  });

  const { data: threadData = [] } = useQuery({
    queryKey: ['threads', from, to],
    queryFn: () => fetchThreadDepth(from, to),
    staleTime: 5 * 60 * 1000,
  });

  const maxHeat = Math.max(...heatmapData.map(c => c.count), 1);

  const formatNum = (n?: number) => {
    if (n === undefined) return '—';
    if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
    return n.toString();
  };

  return (
    <div className="dashboard animate-fade-in">
      {/* KPI Strip */}
      <div className="dashboard__kpi-grid">
        <StatCard
          title="Total Emails"
          value={loadingSummary ? '…' : formatNum(summary?.total_emails)}
          icon={<EnvelopeIcon width={16} />}
          color="purple"
          subtitle="All time"
          delay={0}
        />
        <StatCard
          title="Unique Senders"
          value={loadingSummary ? '…' : formatNum(summary?.total_senders)}
          icon={<UsersIcon width={16} />}
          color="blue"
          subtitle="Distinct addresses"
          delay={60}
        />
        <StatCard
          title="Labels"
          value={loadingSummary ? '…' : summary?.total_labels ?? '—'}
          icon={<TagIcon width={16} />}
          color="cyan"
          subtitle="Gmail categories"
          delay={120}
        />
        <StatCard
          title="Threads"
          value={loadingSummary ? '…' : formatNum(summary?.total_threads)}
          icon={<ChatBubbleBottomCenterTextIcon width={16} />}
          color="green"
          subtitle="Conversations"
          delay={180}
        />
        <StatCard
          title="Avg/Day"
          value={loadingSummary ? '…' : summary?.avg_emails_per_day?.toFixed(1) ?? '—'}
          icon={<ArrowTrendingUpIcon width={16} />}
          color="amber"
          subtitle="Emails received"
          delay={240}
        />
        <StatCard
          title="Busiest Hour"
          value={loadingSummary ? '…' : summary ? `${summary.busiest_hour}:00` : '—'}
          icon={<ClockIcon width={16} />}
          color="rose"
          subtitle="Peak activity time"
          delay={300}
        />
        <StatCard
          title="Unread"
          value={loadingSummary ? '…' : formatNum(summary?.unread_count)}
          icon={<EyeIcon width={16} />}
          color="rose"
          subtitle="Pending emails"
          delay={360}
        />
        <StatCard
          title="Starred"
          value={loadingSummary ? '…' : formatNum(summary?.starred_count)}
          icon={<StarIcon width={16} />}
          color="amber"
          subtitle="Important emails"
          delay={420}
        />
      </div>

      {/* Charts row 1 */}
      <div className="dashboard__charts-row">
        {/* Volume over time */}
        <div className="dashboard__chart-card dashboard__chart-card--wide">
          <div className="dashboard__chart-header">
            <div>
              <h3 className="dashboard__chart-title">Email Volume Over Time</h3>
              <p className="dashboard__chart-sub">Daily received count</p>
            </div>
            <ChartBarSquareIcon width={18} className="dashboard__chart-icon" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={volume} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="volGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#7c5cfc" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#7c5cfc" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#dee2e6" />
              <XAxis dataKey="date" tick={{ fontSize: 10, fill: 'var(--text-muted)' }}
                tickFormatter={(v: string) => v.slice(5)} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Area type="monotone" dataKey="count" name="Emails" stroke="#7c5cfc"
                strokeWidth={2} fill="url(#volGrad)" dot={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Label pie chart */}
        <div className="dashboard__chart-card">
          <div className="dashboard__chart-header">
            <div>
              <h3 className="dashboard__chart-title">By Label</h3>
              <p className="dashboard__chart-sub">Category distribution</p>
            </div>
            <TagIcon width={18} className="dashboard__chart-icon" />
          </div>
          <ResponsiveContainer width="100%" height={180}>
            <PieChart>
              <Pie data={labels} dataKey="count" nameKey="label" cx="50%" cy="50%"
                innerRadius={45} outerRadius={75} paddingAngle={2}>
                {labels.map((_, i) => (
                  <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                ))}
              </Pie>
              <Tooltip
                formatter={(v: unknown, n: unknown) => [String(v), String(n)]}
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border-medium)', borderRadius: 10 }}
                labelStyle={{ color: 'var(--text-secondary)' }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
            </PieChart>
          </ResponsiveContainer>
          <div className="dashboard__legend">
            {labels.slice(0, 5).map((l, i) => (
              <div key={l.label} className="dashboard__legend-item">
                <span className="dashboard__legend-dot" style={{ background: PALETTE[i % PALETTE.length] }} />
                <span className="dashboard__legend-name">{l.label}</span>
                <span className="dashboard__legend-pct">{l.percentage.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts row 2 */}
      <div className="dashboard__charts-row">
        {/* Top senders */}
        <div className="dashboard__chart-card dashboard__chart-card--wide">
          <div className="dashboard__chart-header">
            <div>
              <h3 className="dashboard__chart-title">Top Senders</h3>
              <p className="dashboard__chart-sub">By volume</p>
            </div>
            <ChartBarIcon width={18} className="dashboard__chart-icon" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={senders} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dee2e6" horizontal={false} />
              <XAxis type="number" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <YAxis type="category" dataKey="domain" width={90} tick={{ fontSize: 11, fill: 'var(--text-secondary)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Emails" radius={[0, 4, 4, 0]}>
                {senders.map((_, i) => (
                  <Cell key={i} fill={PALETTE[i % PALETTE.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Thread depth */}
        <div className="dashboard__chart-card">
          <div className="dashboard__chart-header">
            <div>
              <h3 className="dashboard__chart-title">Thread Depth</h3>
              <p className="dashboard__chart-sub">Reply distribution</p>
            </div>
            <ChatBubbleBottomCenterTextIcon width={18} className="dashboard__chart-icon" />
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={threadData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dee2e6" />
              <XAxis dataKey="depth" tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <YAxis tick={{ fontSize: 10, fill: 'var(--text-muted)' }} />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="count" name="Threads" fill="#4f9cf9" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Heatmap */}
      <div className="dashboard__chart-card dashboard__heatmap-card animate-fade-in" style={{ animationDelay: '200ms' }}>
        <div className="dashboard__chart-header">
          <div>
            <h3 className="dashboard__chart-title">Activity Heatmap</h3>
            <p className="dashboard__chart-sub">Emails by hour × day of week</p>
          </div>
          <ChartBarSquareIcon width={18} className="dashboard__chart-icon" />
        </div>
        <div className="heatmap">
          <div className="heatmap__y-labels">
            {DAYS.map(d => <div key={d} className="heatmap__y-label">{d}</div>)}
          </div>
          <div className="heatmap__grid">
            {DAYS.map((_, day) => (
              <div key={day} className="heatmap__row">
                {Array.from({ length: 24 }, (__, hour) => {
                  const cell = heatmapData.find(c => c.day === day && c.hour === hour);
                  const intensity = cell ? cell.count / maxHeat : 0;
                  return (
                    <div
                      key={hour}
                      className="heatmap__cell"
                      title={`${DAYS[day]} ${HOURS[hour]}: ${cell?.count ?? 0} emails`}
                      style={{ '--intensity': intensity } as React.CSSProperties}
                    />
                  );
                })}
              </div>
            ))}
          </div>
        </div>
        <div className="heatmap__x-labels">
          {Array.from({ length: 24 }, (_, i) => (
            <div key={i} className="heatmap__x-label">{i % 3 === 0 ? `${i}h` : ''}</div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
