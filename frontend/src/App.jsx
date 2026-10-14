import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Menu, Cpu } from 'lucide-react';
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

  const refreshSystemData = async () => {
    try {
      const healthRes = await axios.get(`${API_BASE_URL}/api/health`, { timeout: 3000 });
      setBackendOnline(healthRes.status === 200);

      const statsRes = await axios.get(`${API_BASE_URL}/api/stats`, { timeout: 3000 });
      setStats(statsRes.data);

      const histRes = await axios.get(`${API_BASE_URL}/api/history`, { timeout: 3000 });
      setHistory(histRes.data || []);
    } catch (err) {
      setBackendOnline(false);
    }
  };

  useEffect(() => {
    refreshSystemData();
    const interval = setInterval(refreshSystemData, 6000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-container">
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
          <span style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff' }}>KESTRAL</span>
        </div>

        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--border-subtle)',
            color: '#fff',
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
