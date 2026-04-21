import React from 'react';
import { AUTH_GOOGLE_URL } from '../api/client';
import './AuthPage.css';

const AuthPage: React.FC = () => {
  const handleGoogleLogin = () => {
    window.location.href = AUTH_GOOGLE_URL;
  };

  return (
    <div className="auth-page">
      <div className="auth-page__nav">
        <div className="auth-page__logo">
          <div className="auth-page__logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M4 7.00005L10.2 11.65C11.2667 12.45 12.7333 12.45 13.8 11.65L20 7" />
              <rect x="3" y="5" width="18" height="14" rx="2" />
            </svg>
          </div>
          <div className="auth-page__logo-text">
            <span>MailLens</span>
            <span className="auth-page__logo-sub">AI PLATFORM</span>
          </div>
        </div>
        <div className="auth-page__nav-link">Log In</div>
      </div>
      
      <div className="auth-page__content">
        <div className="auth-page__left animate-fade-in-up">
          <h1 className="auth-page__title">Simplify Email <br/>Analysis with AI</h1>
          <p className="auth-page__desc">Sign up or log in to analyze<br/>your inbox with AI-powered insights:</p>
          
          <button className="auth-page__google-btn" onClick={handleGoogleLogin}>
            <svg viewBox="0 0 24 24" className="auth-page__google-icon">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            Continue with Google
          </button>
          
          <p className="auth-page__disclaimer">Read-only access to your emails — your data stays private.</p>
        </div>
        
        <div className="auth-page__right animate-float">
          <div className="auth-page__hexagon">
            <div className="auth-page__hex-inner">
               <div className="auth-page__hex-laurel">~ ❦ ~</div>
               <div className="auth-page__hex-title">MAIL LENS</div>
               <div className="auth-page__hex-sub">AI-Powered Email Insights</div>
               <div className="auth-page__hex-laurel">~ ❦ ~</div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="auth-page__footer">
        Privacy Policy · Terms of Service · © 2026 MailLens
      </div>
    </div>
  );
};

export default AuthPage;
