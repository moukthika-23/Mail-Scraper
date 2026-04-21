import React from 'react';
import './StatCard.css';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'purple' | 'blue' | 'green' | 'amber' | 'rose' | 'cyan';
  trend?: { value: number; label: string };
  delay?: number;
}

const StatCard: React.FC<StatCardProps> = ({
  title, value, subtitle, icon, color = 'purple', trend, delay = 0,
}) => {
  return (
    <div
      className={`stat-card stat-card--${color} animate-fade-in`}
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className="stat-card__header">
        <span className="stat-card__label">{title}</span>
        <div className={`stat-card__icon stat-card__icon--${color}`}>{icon}</div>
      </div>
      <div className="stat-card__value">{value}</div>
      {subtitle && <div className="stat-card__subtitle">{subtitle}</div>}
      {trend && (
        <div className={`stat-card__trend ${trend.value >= 0 ? 'stat-card__trend--up' : 'stat-card__trend--down'}`}>
          <span>{trend.value >= 0 ? '↑' : '↓'} {Math.abs(trend.value)}%</span>
          <span className="stat-card__trend-label">{trend.label}</span>
        </div>
      )}
    </div>
  );
};

export default StatCard;
