import React, { useState, useRef, useEffect } from 'react';
import { useMutation } from '@tanstack/react-query';
import { MagnifyingGlassIcon, SparklesIcon, ClockIcon, XMarkIcon, FunnelIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { searchEmails } from '../api/search';
import { useAppStore } from '../store/appStore';
import type { SearchResponse, EmailCard } from '../types';
import './SearchPage.css';

const HOUR_DIFF = (dateStr: string) => {
  const diff = Date.now() - new Date(dateStr).getTime();
  const h = Math.floor(diff / 3600000);
  if (h < 1) return 'Just now';
  if (h < 24) return `${h}h ago`;
  const d = Math.floor(h / 24);
  if (d < 30) return `${d}d ago`;
  return `${Math.floor(d / 30)}mo ago`;
};

const LABEL_COLOR: Record<string, string> = {
  INBOX: 'purple',
  Important: 'amber',
  Starred: 'amber',
  Promotions: 'blue',
  Social: 'green',
  Updates: 'cyan',
  Spam: 'rose',
};

const SUGGESTION_PROMPTS = [
  'Emails from my manager last month',
  'Unread newsletters this week',
  'GitHub notifications about pull requests',
  'Invoice or payment emails',
  'Meeting invites for next week',
  'Emails about shipping or orders',
];

const EmailResultCard: React.FC<{ email: EmailCard; index: number }> = ({ email, index }) => (
  <div
    className="email-card animate-fade-in"
    style={{ animationDelay: `${index * 60}ms` }}
    id={`email-result-${email.id}`}
  >
    <div className="email-card__avatar">
      {email.sender_name.charAt(0).toUpperCase()}
    </div>
    <div className="email-card__body">
      <div className="email-card__header">
        <span className="email-card__sender">{email.sender_name}</span>
        <span className="email-card__date">{HOUR_DIFF(email.date)}</span>
      </div>
      <div className="email-card__subject">{email.subject}</div>
      <div className="email-card__snippet">{email.snippet}</div>
      <div className="email-card__footer">
        <div className="email-card__labels">
          {email.labels.map((l) => (
            <span key={l} className={`badge badge-${LABEL_COLOR[l] ?? 'muted'}`}>{l}</span>
          ))}
        </div>
        {email.relevance_score && (
          <span className="email-card__score">
            {(email.relevance_score * 100).toFixed(0)}% match
          </span>
        )}
      </div>
    </div>
  </div>
);

const SearchPage: React.FC = () => {
  const { recentQueries, addRecentQuery } = useAppStore();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<SearchResponse | null>(null);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const { mutate: doSearch, isPending } = useMutation({
    mutationFn: (q: string) => searchEmails({ query: q, top_k: 10 }),
    onSuccess: (data) => setResult(data),
  });

  const handleSearch = (q: string) => {
    if (!q.trim()) return;
    addRecentQuery(q.trim());
    setShowSuggestions(false);
    doSearch(q.trim());
  };

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className="search-page animate-fade-in">
      {/* Search bar */}
      <div className="search-page__bar-wrap">
        <div className={`search-page__bar ${isPending ? 'search-page__bar--loading' : ''}`}>
          <MagnifyingGlassIcon width={20} className="search-page__bar-icon" />
          <input
            ref={inputRef}
            id="search-main-input"
            className="search-page__input"
            placeholder="Ask anything about your inbox…"
            value={query}
            onChange={(e) => { setQuery(e.target.value); setShowSuggestions(true); }}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
            onFocus={() => setShowSuggestions(true)}
            onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
            autoComplete="off"
          />
          {query && (
            <button className="search-page__clear" onClick={() => { setQuery(''); setResult(null); }}>
              <XMarkIcon width={14} />
            </button>
          )}
          <button
            id="search-submit-btn"
            className={`search-page__submit ${isPending ? 'search-page__submit--loading' : ''}`}
            onClick={() => handleSearch(query)}
            disabled={isPending}
          >
            {isPending ? <span className="search-page__dots"><span/><span/><span/></span> : <SparklesIcon width={16} />}
            <span>{isPending ? 'Thinking…' : 'Search'}</span>
          </button>
        </div>

        {/* Dropdown — suggestions */}
        {showSuggestions && (
          <div className="search-page__dropdown animate-fade-in">
            {recentQueries.length > 0 && (
              <>
                <div className="search-page__dropdown-section">Recent</div>
                {recentQueries.slice(0, 4).map((q) => (
                  <button key={q} className="search-page__dropdown-item" onMouseDown={() => { setQuery(q); handleSearch(q); }}>
                    <ClockIcon width={13} /> {q}
                  </button>
                ))}
              </>
            )}
            <div className="search-page__dropdown-section">Suggestions</div>
            {SUGGESTION_PROMPTS.slice(0, 4).map((p) => (
              <button key={p} className="search-page__dropdown-item" onMouseDown={() => { setQuery(p); handleSearch(p); }}>
                <SparklesIcon width={13} /> {p}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Suggestion chips (empty state) */}
      {!result && !isPending && (
        <div className="search-page__chips animate-fade-in">
          <p className="search-page__chips-label">Try asking:</p>
          <div className="search-page__chips-list">
            {SUGGESTION_PROMPTS.map((p) => (
              <button key={p} className="search-page__chip" onClick={() => { setQuery(p); handleSearch(p); }}>
                {p}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {isPending && (
        <div className="search-page__skeleton">
          <div className="search-page__answer-skeleton glass-card">
            <div className="skeleton" style={{ height: 14, width: '60%', marginBottom: 10 }} />
            <div className="skeleton" style={{ height: 12, width: '100%', marginBottom: 6 }} />
            <div className="skeleton" style={{ height: 12, width: '85%', marginBottom: 6 }} />
            <div className="skeleton" style={{ height: 12, width: '70%' }} />
          </div>
          {[1,2,3].map(i => (
            <div key={i} className="email-card glass-card">
              <div className="skeleton" style={{ width: 40, height: 40, borderRadius: '50%', flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div className="skeleton" style={{ height: 12, width: '40%', marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 14, width: '75%', marginBottom: 8 }} />
                <div className="skeleton" style={{ height: 11, width: '90%' }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Results */}
      {result && !isPending && (
        <div className="search-page__results">
          {/* Answer card */}
          <div className="search-page__answer animate-fade-in">
            <div className="search-page__answer-header">
              <SparklesIcon width={16} className="search-page__answer-icon" />
              <span>AI Answer</span>
              <span className="search-page__query-time">{result.query_time_ms}ms</span>
            </div>
            <p className="search-page__answer-text">{result.answer}</p>
          </div>

          {/* Result filter bar */}
          <div className="search-page__filter-bar">
            <span className="search-page__result-count">
              {result.sources.length} source{result.sources.length !== 1 ? 's' : ''} found
            </span>
            <button className="search-page__filter-btn" id="search-filter-btn">
              <FunnelIcon width={13} /> Filter <ChevronDownIcon width={13} />
            </button>
          </div>

          {/* Email cards */}
          <div className="search-page__email-list">
            {result.sources.map((email, i) => (
              <EmailResultCard key={email.id} email={email} index={i} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchPage;
