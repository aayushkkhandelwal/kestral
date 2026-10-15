import React from 'react';
import { 
  ShieldCheck, 
  Cpu, 
  Video, 
  Search, 
  ArrowRight, 
  Layers, 
  Sparkles, 
  Clock, 
  CheckCircle2, 
  Sliders, 
  Lock,
  Camera,
  Activity,
  CreditCard,
  Terminal,
  Sun,
  Moon
} from 'lucide-react';

export default function LandingPage({ 
  onEnterApp, 
  onNavigateToAnalysis, 
  onNavigateToEvidence, 
  onNavigateToSearch,
  onNavigateToTransactions,
  onNavigateToLiveCamera,
  stats,
  backendOnline,
  theme = 'dark',
  toggleTheme
}) {
  return (
    <div className="landing-wrapper">
      {/* Ambient background glows */}
      <div className="landing-glow-top" />
      <div className="landing-glow-center" />

      {/* Floating Modern Header */}
      <nav className="landing-navbar glass-panel">
        <div className="landing-brand">
          <div className="landing-logo-icon">
            <Cpu size={22} color="#ffffff" />
          </div>
          <div className="landing-brand-text">
            <span className="brand-title">KESTRAL</span>
            <span className="brand-subtitle">ATM FORENSICS AI</span>
          </div>
        </div>

        <div className="landing-nav-links">
          <a href="#features">Capabilities</a>
          <a href="#pipeline">Architecture</a>
          <a href="#quality">Quality v2</a>
          <a href="#forensics">Biometrics</a>
        </div>

        <div className="landing-nav-actions">
          {toggleTheme && (
            <button
              onClick={toggleTheme}
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
              style={{
                background: 'rgba(255, 255, 255, 0.05)',
                border: '1px solid rgba(168, 85, 247, 0.25)',
                color: 'var(--text-primary)',
                borderRadius: '9999px',
                padding: '8px 12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer'
              }}
            >
              {theme === 'dark' ? (
                <Sun size={16} color="var(--accent-amber)" />
              ) : (
                <Moon size={16} color="var(--accent-purple)" />
              )}
            </button>
          )}

          <div className="status-indicator-pill">
            <span className={`status-dot ${backendOnline ? 'online' : 'offline'}`} />
            <span>{backendOnline ? 'ENGINE READY' : 'OFFLINE'}</span>
          </div>
          <button 
            className="btn btn-primary landing-cta-btn"
            onClick={onEnterApp}
          >
            <span>Launch Mission Control</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </nav>

      {/* Hero Section */}
      <header className="landing-hero">
        <div className="hero-badge">
          <Sparkles size={14} className="hero-badge-icon" />
          <span>HACKATHON PROBLEM SKIT001 • AI FORENSIC INTELLIGENCE</span>
        </div>

        <h1 className="hero-main-title">
          EVIDENCE-GRADE FORENSICS FOR ATM SURVEILLANCE
        </h1>

        <p className="hero-subtitle">
          Transforming challenging CCTV footage into court-admissible evidence with Quality v2 best-frame extraction, 
          spatiotemporal transaction linking, and 128D biometric identification.
        </p>

        <div className="hero-cta-group">
          <button 
            className="btn btn-primary hero-btn-large"
            onClick={onEnterApp}
          >
            <span>Launch Mission Control</span>
            <ArrowRight size={18} />
          </button>
          <button 
            className="btn btn-secondary hero-btn-outline"
            onClick={onNavigateToAnalysis}
          >
            <Video size={18} />
            <span>Analyze Video Feed</span>
          </button>
        </div>

        {/* Futuristic Cityscape Illustration Vector Matching Rw Studio Aesthetic */}
        <div className="hero-cityscape-container">
          <svg 
            className="hero-cityscape-svg" 
            viewBox="0 0 1400 380" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="skyGlow" x1="700" y1="0" x2="700" y2="380" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#7928ca" stopOpacity="0.45" />
                <stop offset="50%" stopColor="#9333ea" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#0c091d" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="buildingDark" x1="0" y1="100" x2="0" y2="380" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#251752" />
                <stop offset="100%" stopColor="#100b26" />
              </linearGradient>
              <linearGradient id="buildingMid" x1="0" y1="60" x2="0" y2="380" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#3b1f7a" />
                <stop offset="100%" stopColor="#160e36" />
              </linearGradient>
              <linearGradient id="buildingGlow" x1="0" y1="40" x2="0" y2="380" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#581c87" />
                <stop offset="40%" stopColor="#3b0764" />
                <stop offset="100%" stopColor="#0f0923" />
              </linearGradient>
              <linearGradient id="accentBeam" x1="0" y1="0" x2="0" y2="380" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#c084fc" stopOpacity="0.9" />
                <stop offset="70%" stopColor="#a855f7" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
              </linearGradient>
              <linearGradient id="cyanHighlight" x1="0" y1="0" x2="0" y2="380" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                <stop offset="100%" stopColor="#6366f1" stopOpacity="0.1" />
              </linearGradient>
            </defs>

            {/* Horizon Glow Backdrop */}
            <rect x="0" y="0" width="1400" height="380" fill="url(#skyGlow)" />

            {/* Distant Spire Background Layer */}
            <path d="M120 380 L120 180 L145 130 L170 180 L170 380 Z" fill="#1b123d" opacity="0.6" />
            <path d="M260 380 L260 160 L290 90 L320 160 L320 380 Z" fill="#201548" opacity="0.7" />
            <path d="M500 380 L500 110 L530 40 L560 110 L560 380 Z" fill="#2c1a63" opacity="0.8" />
            <path d="M820 380 L820 120 L845 30 L870 120 L870 380 Z" fill="#2c1a63" opacity="0.8" />
            <path d="M1040 380 L1040 150 L1070 80 L1100 150 L1100 380 Z" fill="#201548" opacity="0.7" />
            <path d="M1240 380 L1240 190 L1265 140 L1290 190 L1290 380 Z" fill="#1b123d" opacity="0.6" />

            {/* Midground Cyberpunk Buildings */}
            <rect x="80" y="220" width="110" height="160" rx="4" fill="url(#buildingDark)" />
            <rect x="180" y="190" width="90" height="190" rx="4" fill="url(#buildingMid)" />
            <rect x="290" y="140" width="130" height="240" rx="4" fill="url(#buildingGlow)" />
            <line x1="290" y1="140" x2="420" y2="140" stroke="#c084fc" strokeWidth="2" opacity="0.8" />
            <line x1="290" y1="140" x2="290" y2="380" stroke="#a855f7" strokeWidth="1" opacity="0.5" />

            {/* Central Landmark Tower Left */}
            <path d="M480 380 L480 180 L520 80 L540 80 L580 180 L580 380 Z" fill="url(#buildingMid)" />
            <path d="M525 80 L530 20 L535 80 Z" fill="url(#accentBeam)" />
            <line x1="530" y1="20" x2="530" y2="0" stroke="#f472b6" strokeWidth="2" />

            {/* Central Megatower Center */}
            <path d="M630 380 L630 140 L670 70 L730 70 L770 140 L770 380 Z" fill="url(#buildingGlow)" />
            <line x1="670" y1="70" x2="730" y2="70" stroke="#38bdf8" strokeWidth="3" />
            <rect x="660" y="110" width="80" height="270" fill="#1e1145" />
            <line x1="700" y1="70" x2="700" y2="380" stroke="url(#cyanHighlight)" strokeWidth="1.5" />

            {/* Central Landmark Tower Right */}
            <path d="M810 380 L810 170 L850 60 L870 60 L910 170 L910 380 Z" fill="url(#buildingMid)" />
            <path d="M855 60 L860 15 L865 60 Z" fill="url(#accentBeam)" />
            <line x1="860" y1="15" x2="860" y2="0" stroke="#38bdf8" strokeWidth="2" />

            {/* Right Blocks */}
            <rect x="960" y="150" width="120" height="230" rx="4" fill="url(#buildingGlow)" />
            <line x1="960" y1="150" x2="1080" y2="150" stroke="#c084fc" strokeWidth="2" opacity="0.8" />
            <rect x="1100" y="190" width="95" height="190" rx="4" fill="url(#buildingMid)" />
            <rect x="1210" y="230" width="120" height="150" rx="4" fill="url(#buildingDark)" />

            {/* Architectural Window Light Grids */}
            <g opacity="0.6">
              <circle cx="310" cy="180" r="2" fill="#c084fc" />
              <circle cx="330" cy="180" r="2" fill="#c084fc" />
              <circle cx="350" cy="180" r="2" fill="#c084fc" />
              <circle cx="370" cy="180" r="2" fill="#c084fc" />
              <circle cx="390" cy="180" r="2" fill="#c084fc" />

              <circle cx="310" cy="210" r="2" fill="#38bdf8" />
              <circle cx="330" cy="210" r="2" fill="#38bdf8" />
              <circle cx="350" cy="210" r="2" fill="#38bdf8" />
              <circle cx="370" cy="210" r="2" fill="#38bdf8" />

              <circle cx="680" cy="160" r="2.5" fill="#f472b6" />
              <circle cx="700" cy="160" r="2.5" fill="#f472b6" />
              <circle cx="720" cy="160" r="2.5" fill="#f472b6" />
              
              <circle cx="680" cy="190" r="2.5" fill="#38bdf8" />
              <circle cx="700" cy="190" r="2.5" fill="#38bdf8" />
              <circle cx="720" cy="190" r="2.5" fill="#38bdf8" />

              <circle cx="980" cy="190" r="2" fill="#c084fc" />
              <circle cx="1000" cy="190" r="2" fill="#c084fc" />
              <circle cx="1020" cy="190" r="2" fill="#c084fc" />
              <circle cx="1040" cy="190" r="2" fill="#c084fc" />

              <circle cx="980" cy="220" r="2" fill="#38bdf8" />
              <circle cx="1000" cy="220" r="2" fill="#38bdf8" />
              <circle cx="1020" cy="220" r="2" fill="#38bdf8" />
              <circle cx="1040" cy="220" r="2" fill="#38bdf8" />
            </g>

            {/* Glowing horizon base light beam */}
            <line x1="0" y1="379" x2="1400" y2="379" stroke="url(#accentBeam)" strokeWidth="3" opacity="0.6" />
          </svg>
        </div>
      </header>

      {/* Metrics Counter Bar */}
      <section className="landing-metrics-bar glass-panel">
        <div className="metric-pill">
          <div className="metric-icon-box">
            <Sliders size={20} color="var(--accent-purple)" />
          </div>
          <div>
            <div className="metric-value">112×112</div>
            <div className="metric-label">Normalized Sharpness</div>
          </div>
        </div>

        <div className="metric-divider" />

        <div className="metric-pill">
          <div className="metric-icon-box">
            <Search size={20} color="var(--accent-cyan)" />
          </div>
          <div>
            <div className="metric-value">128-D</div>
            <div className="metric-label">SFace Cosine Vectors</div>
          </div>
        </div>

        <div className="metric-divider" />

        <div className="metric-pill">
          <div className="metric-icon-box">
            <Clock size={20} color="var(--accent-magenta)" />
          </div>
          <div>
            <div className="metric-value">±10s</div>
            <div className="metric-label">Targeted Windowing</div>
          </div>
        </div>

        <div className="metric-divider" />

        <div className="metric-pill">
          <div className="metric-icon-box">
            <Lock size={20} color="var(--accent-emerald)" />
          </div>
          <div>
            <div className="metric-value">100%</div>
            <div className="metric-label">Tamper-Evident Ledger</div>
          </div>
        </div>
      </section>

      {/* Core Capabilities Section */}
      <section id="features" className="landing-section">
        <div className="section-header-centered">
          <span className="section-eyebrow">INTELLIGENT FORENSICS</span>
          <h2 className="section-title">Built for Challenging ATM Surveillance Footage</h2>
          <p className="section-description">
            Standard video players and basic face detectors fail on real-world CCTV. 
            Kestral combines state-of-the-art vision pipelines with legal audit integrity.
          </p>
        </div>

        <div className="feature-grid">
          {/* Card 1 */}
          <div className="feature-card glass-panel">
            <div className="feature-card-glow" />
            <div className="feature-icon" style={{ background: 'rgba(168, 85, 247, 0.15)', color: 'var(--accent-purple)' }}>
              <Sparkles size={24} />
            </div>
            <h3 className="feature-heading">Quality v2 Best-Frame Arbiter</h3>
            <p className="feature-body">
              Eliminates noisy and blurry small crops. Normalizes faces to 112×112 before Laplacian variance scoring, 
              estimates 5-point landmark yaw/pitch symmetry, and balances exposure with CLAHE.
            </p>
            <div className="feature-tag-list">
              <span className="feature-tag">Pose Proxy</span>
              <span className="feature-tag">Normalized Laplacian</span>
              <span className="feature-tag">CLAHE Low-Light</span>
            </div>
          </div>

          {/* Card 2 */}
          <div className="feature-card glass-panel">
            <div className="feature-card-glow" />
            <div className="feature-icon" style={{ background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-cyan)' }}>
              <CreditCard size={24} />
            </div>
            <h3 className="feature-heading">Spatiotemporal Foot-Dwell Linking</h3>
            <p className="feature-body">
              Calculates person foot positions and applies ray-casting point-in-polygon tests inside user-drawn ATM interaction zones. 
              Automatically detects and flags queue ambiguity.
            </p>
            <div className="feature-tag-list">
              <span className="feature-tag">ROI Polygon Canvas</span>
              <span className="feature-tag">Dwell Time Scoring</span>
              <span className="feature-tag">Ambiguity Flagging</span>
            </div>
          </div>

          {/* Card 3 */}
          <div className="feature-card glass-panel">
            <div className="feature-card-glow" />
            <div className="feature-icon" style={{ background: 'rgba(217, 70, 239, 0.15)', color: 'var(--accent-magenta)' }}>
              <Layers size={24} />
            </div>
            <h3 className="feature-heading">AI Deblur & Panoramic Plates</h3>
            <p className="feature-body">
              Dual-stage unsharp masking (USM) with bilateral edge restoration restores eye and mouth contours. 
              Synthesizes Profile A, exposure-fused portrait, and Profile B into a biometric composite.
            </p>
            <div className="feature-tag-list">
              <span className="feature-tag">USM Sharpening</span>
              <span className="feature-tag">Bilateral Smoothing</span>
              <span className="feature-tag">Mertens Detail Fusion</span>
            </div>
          </div>
        </div>
      </section>

      {/* Interactive Architecture Section */}
      <section id="pipeline" className="landing-section">
        <div className="section-header-centered">
          <span className="section-eyebrow">AUTOMATED WORKFLOW</span>
          <h2 className="section-title">From Raw CCTV to Legal Evidence Dossier</h2>
          <p className="section-description">
            Asynchronous multi-worker architecture powered by FastAPI, PyTorch, OpenCV DNN, and SQLite.
          </p>
        </div>

        <div className="pipeline-steps-container glass-panel">
          <div className="pipeline-step">
            <div className="step-number">01</div>
            <div className="step-content">
              <h4>Targeted Windowing</h4>
              <p>Direct timestamp seek (e.g. ±10s around transaction) bypassing hour-long video files in seconds.</p>
            </div>
          </div>

          <div className="pipeline-connector" />

          <div className="pipeline-step">
            <div className="step-number">02</div>
            <div className="step-content">
              <h4>YOLOv8 + ByteTrack</h4>
              <p>Persistent human tracking with trajectory foot coordinate sampling and tracker isolation per video.</p>
            </div>
          </div>

          <div className="pipeline-connector" />

          <div className="pipeline-step">
            <div className="step-number">03</div>
            <div className="step-content">
              <h4>YuNet Face Geometry</h4>
              <p>5 facial landmarks detection confirming real biological faces over the back of heads or hats.</p>
            </div>
          </div>

          <div className="pipeline-connector" />

          <div className="pipeline-step">
            <div className="step-number">04</div>
            <div className="step-content">
              <h4>Quality v2 Scoring</h4>
              <p>Weighted scoring combining normalized Laplacian sharpness, resolution, exposure, and pose symmetry.</p>
            </div>
          </div>

          <div className="pipeline-connector" />

          <div className="pipeline-step">
            <div className="step-number">05</div>
            <div className="step-content">
              <h4>Forensic Synthesis</h4>
              <p>Dual-stage deblurring, runner-up reels, SFace 128D embedding indexing, and transaction linking.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Live CTA Banner */}
      <section className="landing-cta-banner glass-panel">
        <div className="cta-banner-content">
          <h2>Ready to Inspect ATM Surveillance Evidence?</h2>
          <p>
            Access the full Kestral investigator dashboard with video analysis, ROI configuration, biometric face search, and live camera detection.
          </p>
          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <button 
              className="btn btn-primary hero-btn-large"
              onClick={onEnterApp}
            >
              <span>Open Mission Control</span>
              <ArrowRight size={18} />
            </button>
            <button 
              className="btn btn-secondary"
              onClick={onNavigateToSearch}
            >
              <Search size={18} />
              <span>Database Face Search</span>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-left">
            <div className="landing-brand">
              <div className="landing-logo-icon" style={{ width: '32px', height: '32px' }}>
                <Cpu size={18} color="#ffffff" />
              </div>
              <span className="brand-title" style={{ fontSize: '1.1rem' }}>KESTRAL</span>
            </div>
            <p className="footer-tagline">
              AI-based Face Identification & Evidence Intelligence for ATM Surveillance.
            </p>
          </div>

          <div className="footer-disclaimer">
            <p>
              <strong>ETHICAL FORENSIC NOTICE:</strong> Facial search yields statistical visual similarity only. 
              Designed as an investigative decision-support tool requiring human verification for legal proceedings.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
