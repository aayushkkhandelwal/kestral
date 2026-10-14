import React from 'react';
import { 
  LayoutDashboard, 
  Video, 
  ShieldCheck, 
  Camera,
  Cpu, 
  Activity, 
  Terminal,
  ExternalLink,
  Sun,
  Moon,
  X 
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function Sidebar({ 
  activePage, 
  setActivePage, 
  backendOnline = true,
  isOpen = false,
  onClose,
  theme = 'dark',
  toggleTheme
}) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'live-camera', label: 'Live Camera', icon: Camera },
    { id: 'analysis', label: 'Video Analysis', icon: Video },
    { id: 'evidence', label: 'Evidence Vault', icon: ShieldCheck },
  ];

  return (
    <aside 
      className={`sidebar-container ${isOpen ? 'open' : ''}`}
      style={{
        width: '280px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        padding: '24px 16px',
        height: '100vh',
        position: 'sticky',
        top: 0,
        flexShrink: 0,
        transition: 'background-color 0.25s ease, border-color 0.25s ease'
      }}
    >
      {/* Brand Header */}
      <div style={{ padding: '0 8px 24px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '10px',
              background: 'linear-gradient(135deg, var(--accent-cyan), var(--accent-indigo))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px var(--accent-cyan-glow)'
            }}>
              <Cpu size={22} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                KESTRAL
              </h1>
              <p style={{ fontSize: '0.68rem', color: 'var(--accent-cyan)', fontWeight: 600, letterSpacing: '0.08em' }}>
                VISION INTELLIGENCE
              </p>
            </div>
          </div>

          {/* Close button for mobile drawer */}
          {onClose && (
            <button
              onClick={onClose}
              style={{
                background: 'var(--bg-input)',
                border: '1px solid var(--border-subtle)',
                color: 'var(--text-secondary)',
                borderRadius: '8px',
                width: '32px',
                height: '32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
            >
              <X size={16} />
            </button>
          )}
        </div>

        {/* Status Pill */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
          padding: '4px 8px',
          background: backendOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
          border: `1px solid ${backendOnline ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)'}`,
          borderRadius: '999px',
          fontSize: '0.72rem',
          color: backendOnline ? '#10b981' : '#f43f5e',
          marginTop: '6px'
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            backgroundColor: backendOnline ? '#10b981' : '#f43f5e',
            boxShadow: backendOnline ? '0 0 8px #10b981' : '0 0 8px #f43f5e'
          }} />
          {backendOnline ? 'ENGINE ONLINE' : 'DISCONNECTED'}
        </div>
      </div>

      {/* Nav Menu */}
      <nav style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activePage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                setActivePage(item.id);
                if (onClose) onClose();
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isActive ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                border: isActive ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid transparent',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.9rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={19} color={isActive ? 'var(--accent-cyan)' : 'currentColor'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Theme Toggle Button */}
      {toggleTheme && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '10px 14px',
          backgroundColor: 'var(--bg-input)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-subtle)',
          marginBottom: '14px',
          cursor: 'pointer',
          userSelect: 'none',
          transition: 'all 0.2s ease'
        }}
        onClick={toggleTheme}
        title={`Toggle to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {theme === 'dark' ? (
              <Moon size={16} color="var(--accent-cyan)" />
            ) : (
              <Sun size={16} color="var(--accent-amber)" />
            )}
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
              {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
            </span>
          </div>

          <div style={{
            width: '38px',
            height: '22px',
            borderRadius: '999px',
            backgroundColor: theme === 'light' ? 'var(--accent-cyan)' : 'rgba(255, 255, 255, 0.15)',
            padding: '2px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: theme === 'light' ? 'flex-end' : 'flex-start',
            transition: 'all 0.2s ease'
          }}>
            <div style={{
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              backgroundColor: '#ffffff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {theme === 'light' ? (
                <Sun size={11} color="#0891b2" />
              ) : (
                <Moon size={11} color="#0f172a" />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Engine Telemetry Card */}
      <div style={{
        padding: '16px',
        backgroundColor: 'var(--bg-input)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        fontSize: '0.75rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>PIPELINE CORES</span>
          <Activity size={14} color="var(--accent-cyan)" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', fontFamily: 'var(--font-mono)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Tracker:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>YOLOv8 ByteTrack</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Biometrics:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>OpenCV Haar</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Fidelity:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Laplacian Var</span>
          </div>
        </div>

        <a
          href={`${API_BASE_URL}/docs`}
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            color: 'var(--accent-cyan)',
            textDecoration: 'none',
            marginTop: '12px',
            paddingTop: '8px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.72rem',
            fontWeight: 600
          }}
        >
          <Terminal size={13} />
          <span>REST API Docs</span>
          <ExternalLink size={11} style={{ marginLeft: 'auto' }} />
        </a>
      </div>
    </aside>
  );
}
