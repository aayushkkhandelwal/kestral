import { 
  Sparkles,
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
  CreditCard,
  Search,
  FileText,
  X 
} from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function Sidebar({ 
  activePage, 
  setActivePage, 
  backendOnline = true,
  healthInfo = null,
  currentUser = 'investigator',
  isOpen = false,
  onClose,
  theme = 'dark',
  toggleTheme
}) {
  const navItems = [
    { id: 'landing', label: 'Landing Page', icon: Sparkles },
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'transactions', label: 'ATM Transactions', icon: CreditCard },
    { id: 'evidence', label: 'Evidence Vault', icon: ShieldCheck },
    { id: 'search', label: 'Face Search', icon: Search },
    { id: 'analysis', label: 'Video Analysis', icon: Video },
    { id: 'live-camera', label: 'Live Camera', icon: Camera },
    { id: 'audit', label: 'Audit Trail', icon: FileText },
  ];

  const cudaText = healthInfo?.cuda_available ? 'CUDA GPU' : 'MPS / CPU Acceleration';
  const personModel = healthInfo?.person_model || 'YOLOv8n ByteTrack';
  const faceModel = healthInfo?.face_model_loaded ? 'YuNet DNN (Loaded)' : 'YuNet DNN';

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
              background: 'linear-gradient(135deg, var(--accent-purple), var(--accent-indigo))',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 16px var(--accent-purple-glow)'
            }}>
              <Cpu size={22} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--text-primary)' }}>
                KESTRAL
              </h1>
              <p style={{ fontSize: '0.68rem', color: 'var(--accent-magenta)', fontWeight: 700, letterSpacing: '0.08em' }}>
                ATM VISION INTELLIGENCE
              </p>
            </div>
          </div>

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

        {/* Status Pill & User Role */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '6px' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 8px',
            background: backendOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
            border: `1px solid ${backendOnline ? 'rgba(16, 185, 129, 0.25)' : 'rgba(244, 63, 94, 0.25)'}`,
            borderRadius: '999px',
            fontSize: '0.72rem',
            color: backendOnline ? 'var(--accent-emerald)' : '#fb7185'
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

          <div style={{
            padding: '2px 8px',
            borderRadius: '999px',
            backgroundColor: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-secondary)',
            fontSize: '0.68rem',
            textTransform: 'uppercase',
            fontWeight: 700
          }}>
            {currentUser}
          </div>
        </div>
      </div>

      {/* Nav Menu */}
      <nav style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '5px', flex: 1, overflowY: 'auto' }}>
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
                padding: '10px 14px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: isActive ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                border: isActive ? '1px solid rgba(6, 182, 212, 0.3)' : '1px solid transparent',
                fontWeight: isActive ? 700 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                textAlign: 'left',
                transition: 'all 0.15s ease'
              }}
            >
              <Icon size={18} color={isActive ? 'var(--accent-cyan)' : 'currentColor'} />
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

      {/* Engine Telemetry Card (Task T0.4 & T0.5) */}
      <div style={{
        padding: '14px',
        backgroundColor: 'var(--bg-input)',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-subtle)',
        fontSize: '0.72rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
          <span style={{ color: 'var(--text-secondary)', fontWeight: 600 }}>PIPELINE TELEMETRY</span>
          <Activity size={13} color="var(--accent-cyan)" />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '3px', fontFamily: 'var(--font-mono)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Compute:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{cudaText}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Detector:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{personModel}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Facial DNN:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{faceModel}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>Fidelity:</span>
            <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>Quality v2 (Laplacian)</span>
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
            marginTop: '10px',
            paddingTop: '8px',
            borderTop: '1px solid var(--border-subtle)',
            fontSize: '0.7rem',
            fontWeight: 600
          }}
        >
          <Terminal size={12} />
          <span>Interactive API Docs</span>
          <ExternalLink size={10} style={{ marginLeft: 'auto' }} />
        </a>
      </div>
    </aside>
  );
}
