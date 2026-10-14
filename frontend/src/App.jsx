import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Menu, Cpu, Sun, Moon } from 'lucide-react';
import { API_BASE_URL } from './config';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import Evidence from './pages/Evidence';
import LiveCamera from './pages/LiveCamera';

export default function App() {
  const [activePage, setActivePage] = useState('dashboard');
  const [backendOnline, setBackendOnline] = useState(false);
  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const failureCountRef = useRef(0);
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('kestral_theme') || 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('kestral_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const refreshSystemData = async () => {
    // 1. Lightweight health ping (dedicated 8s timeout)
    try {
      const healthRes = await axios.get(`${API_BASE_URL}/api/health`, { timeout: 8000 });
      if (healthRes.status === 200) {
        failureCountRef.current = 0;
        setBackendOnline(true);
      }
    } catch {
      failureCountRef.current += 1;
      // Tolerate transient 1-cycle latency spikes under heavy CPU load
      if (failureCountRef.current >= 2) {
        setBackendOnline(false);
      }
    }

    // 2. Auxiliary dashboard data (independent from health ping)
    try {
      const [statsRes, histRes] = await Promise.allSettled([
        axios.get(`${API_BASE_URL}/api/stats`, { timeout: 8000 }),
        axios.get(`${API_BASE_URL}/api/history`, { timeout: 8000 })
      ]);

      if (statsRes.status === 'fulfilled') {
        setStats(statsRes.value.data);
      }
      if (histRes.status === 'fulfilled') {
        setHistory(histRes.value.data || []);
      }
    } catch {
      // Ignore background telemetry errors
    }
  };

  useEffect(() => {
    refreshSystemData();
    const interval = setInterval(refreshSystemData, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container" data-theme={theme}>
      {/* Mobile Top App Bar */}
      <div className="mobile-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-indigo))',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <Cpu size={18} color="#fff" />
          </div>
          <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-primary)' }}>KESTRAL</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
            style={{
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              borderRadius: '8px',
              padding: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            {theme === 'dark' ? (
              <Sun size={18} color="var(--accent-amber)" />
            ) : (
              <Moon size={18} color="var(--accent-cyan)" />
            )}
          </button>

          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            style={{
              background: 'var(--bg-input)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--text-primary)',
              borderRadius: '8px',
              padding: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
          >
            <Menu size={20} />
          </button>
        </div>
      </div>

      {/* Backdrop for mobile drawer */}
      {mobileMenuOpen && (
        <div 
          className="mobile-overlay"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Navigation Sidebar */}
      <Sidebar
        activePage={activePage}
        setActivePage={(page) => {
          setActivePage(page);
          setMobileMenuOpen(false);
        }}
        backendOnline={backendOnline}
        isOpen={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
        theme={theme}
        toggleTheme={toggleTheme}
      />

      {/* Main Dynamic Viewport */}
      <main className="main-content">
        {activePage === 'dashboard' && (
          <Dashboard
            stats={stats}
            history={history}
            onNavigateToAnalysis={() => setActivePage('analysis')}
            onNavigateToEvidence={() => setActivePage('evidence')}
            onNavigateToLiveCamera={() => setActivePage('live-camera')}
          />
        )}

        {activePage === 'live-camera' && (
          <LiveCamera />
        )}

        {activePage === 'analysis' && (
          <Analysis onRefreshStats={refreshSystemData} />
        )}

        {activePage === 'evidence' && (
          <Evidence />
        )}
      </main>
    </div>
  );
}
