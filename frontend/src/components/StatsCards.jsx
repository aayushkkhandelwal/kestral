import React from 'react';
import { Users, Film, Award, Sparkles } from 'lucide-react';

export default function StatsCards({ stats }) {
  const avgFidelity = stats?.system_average_fidelity != null
    ? `${stats.system_average_fidelity}%`
    : 'No Data';

  const cards = [
    {
      title: 'Videos Processed',
      value: stats?.total_videos_analyzed ?? 0,
      icon: Film,
      color: 'var(--accent-cyan)',
      glow: 'var(--accent-cyan-glow)',
      sub: 'Surveillance Streams'
    },
    {
      title: 'Persons Tracked',
      value: stats?.total_persons_tracked ?? 0,
      icon: Users,
      color: 'var(--accent-indigo)',
      glow: 'var(--accent-indigo-glow)',
      sub: 'Unique Track IDs'
    },
    {
      title: 'High-Fidelity Evidence',
      value: stats?.high_quality_evidence_captured ?? 0,
      icon: Award,
      color: 'var(--accent-emerald)',
      glow: 'var(--accent-emerald-glow)',
      sub: 'Optimal Facial Crops'
    },
    {
      title: 'Avg Evidence Quality',
      value: avgFidelity,
      icon: Sparkles,
      color: 'var(--accent-amber)',
      glow: 'rgba(245, 158, 11, 0.2)',
      sub: 'Laplacian & Clarity Score'
    }
  ];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
      gap: '20px',
      marginBottom: '32px'
    }}>
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="glass-panel"
            style={{
              padding: '22px',
              position: 'relative',
              overflow: 'hidden'
            }}
          >
            {/* Top Row: Icon & Sub */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
              <div style={{
                width: '42px',
                height: '42px',
                borderRadius: '12px',
                backgroundColor: 'var(--bg-input)',
                border: `1px solid ${card.color}40`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 12px ${card.glow}`
              }}>
                <Icon size={22} color={card.color} />
              </div>

              <span style={{
                fontSize: '0.72rem',
                fontFamily: 'var(--font-mono)',
                color: 'var(--text-muted)',
                padding: '2px 8px',
                borderRadius: '4px',
                background: 'var(--bg-input)'
              }}>
                {card.sub}
              </span>
            </div>

            {/* Value */}
            <div style={{
              fontSize: '2rem',
              fontWeight: 800,
              letterSpacing: '-0.03em',
              color: 'var(--text-primary)',
              lineHeight: 1.1,
              marginBottom: '4px'
            }}>
              {card.value}
            </div>

            {/* Label */}
            <div style={{
              fontSize: '0.825rem',
              color: 'var(--text-secondary)',
              fontWeight: 500
            }}>
              {card.title}
            </div>

            {/* Bottom decorative accent */}
            <div style={{
              position: 'absolute',
              bottom: 0,
              left: '10%',
              right: '10%',
              height: '2px',
              background: `linear-gradient(90deg, transparent, ${card.color}, transparent)`,
              opacity: 0.6
            }} />
          </div>
        );
      })}
    </div>
  );
}
