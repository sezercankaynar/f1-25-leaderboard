import { useEffect, useRef, useState } from 'react';
import {
  TEAMS,
  SECTOR_COLORS,
  COMPOUND_COLORS,
  ERS_MODE_COLORS,
  ERS_MODE_LABELS,
} from './constants.js';

export function TeamCrest({ team, size = 16 }) {
  const t = TEAMS[team];
  if (!t) return null;
  const glyphs = {
    APX: <path d="M8 2 L14 14 L2 14 Z" />,
    VLK: <path d="M2 8 L8 2 L14 8 L8 14 Z" />,
    NRD: <path d="M2 4 L14 4 L14 12 L2 12 Z M2 8 L14 8" stroke="#0b0b0f" strokeWidth="1.2" fill="none" />,
    KRN: <path d="M8 1.5 L9.8 6 L14.5 6 L10.7 9 L12.2 13.5 L8 10.8 L3.8 13.5 L5.3 9 L1.5 6 L6.2 6 Z" />,
    ORB: <g><circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" /><circle cx="8" cy="8" r="1.6" /></g>,
    SLC: <path d="M3 3 H13 V6 L9 8 L13 10 V13 H3 V10 L7 8 L3 6 Z" />,
    TRN: <path d="M2 13 Q5 3 14 3 Q11 8 14 13 Q9 10 2 13 Z" />,
    VRT: <path d="M2 3 H14 L9 13 H7 Z" />,
    MRD: <g><rect x="3" y="3" width="4" height="10" /><rect x="9" y="3" width="4" height="10" /></g>,
    HLX: <path d="M2 2 Q8 8 14 2 M2 8 Q8 14 14 8 M2 14 Q8 8 14 14" stroke="currentColor" strokeWidth="1.5" fill="none" />,
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 16 16"
      style={{ color: t.color, fill: t.color, flexShrink: 0 }}
      aria-label={t.name}
    >
      {glyphs[team]}
    </svg>
  );
}

export function SectorBars({ sectors, height = 10, width = 7, gap = 3 }) {
  return (
    <div style={{ display: 'flex', gap: `${gap}px`, alignItems: 'center' }}>
      {sectors.map((s, i) => (
        <div
          key={i}
          style={{
            width: `${width}px`,
            height: `${height}px`,
            borderRadius: '1px',
            background: SECTOR_COLORS[s],
            transition: 'background 180ms',
          }}
        />
      ))}
    </div>
  );
}

export function TireCompact({ compound, wear, laps }) {
  const color = COMPOUND_COLORS[compound];
  const r = 9;
  const circ = 2 * Math.PI * r;
  const remaining = Math.max(0, 100 - wear) / 100;
  const dash = circ * remaining;
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{ position: 'relative', width: 22, height: 22 }}>
        <svg width="22" height="22">
          <circle cx="11" cy="11" r={r} fill="none" stroke="#2A2A30" strokeWidth="2" />
          <circle
            cx="11" cy="11" r={r}
            fill="none" stroke={color} strokeWidth="2.4"
            strokeDasharray={`${dash} ${circ}`}
            strokeLinecap="round"
            transform="rotate(-90 11 11)"
            style={{ transition: 'stroke-dasharray 220ms' }}
          />
          <text x="11" y="14" textAnchor="middle" fontSize="9" fontWeight="800"
            fill={color} fontFamily="'Rajdhani', sans-serif">{compound}</text>
        </svg>
      </div>
      <span style={{
        fontSize: 10, fontWeight: 700, color: '#9AA0A6',
        fontFamily: "'Rajdhani', sans-serif", letterSpacing: 0.5,
        minWidth: 14, textAlign: 'left',
      }}>{laps}</span>
    </div>
  );
}

export function ErsCompact({ ers, mode }) {
  const modeColor = ERS_MODE_COLORS[mode] || '#5A6168';
  const label = ERS_MODE_LABELS[mode] || 'OFF';
  const pct = Math.max(0, Math.min(100, ers));
  const barColor = pct < 20 ? '#E11D2E' : pct < 40 ? '#F6C416' : '#2AD9E6';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      <div style={{
        width: 22, height: 10,
        background: '#1A1A20',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 1,
        position: 'relative',
        padding: 1,
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: barColor,
          transition: 'width 220ms, background 220ms',
        }} />
        <div style={{
          position: 'absolute', right: -2, top: 2, bottom: 2,
          width: 2, background: 'rgba(255,255,255,0.15)',
          borderRadius: 1,
        }} />
      </div>
      <span style={{
        fontSize: 9, fontWeight: 800, letterSpacing: 0.6,
        color: modeColor,
        fontFamily: "'Rajdhani', sans-serif",
        minWidth: 22, textAlign: 'left',
      }}>{label}</span>
    </div>
  );
}

export function usePositionDeltas(drivers, flashMs = 2200) {
  const prevRef = useRef(null);
  const [flashes, setFlashes] = useState({});
  useEffect(() => {
    const prev = prevRef.current;
    const curr = {};
    drivers.forEach(d => { curr[d.code] = d.pos; });
    if (prev) {
      const newFlashes = {};
      let hasAny = false;
      drivers.forEach(d => {
        const oldPos = prev[d.code];
        if (oldPos != null && oldPos !== d.pos) {
          newFlashes[d.code] = { delta: oldPos - d.pos, at: Date.now() };
          hasAny = true;
        }
      });
      if (hasAny) {
        setFlashes(f => ({ ...f, ...newFlashes }));
        const t = setTimeout(() => {
          setFlashes(f => {
            const out = {};
            const now = Date.now();
            Object.entries(f).forEach(([k, v]) => {
              if (now - v.at < flashMs) out[k] = v;
            });
            return out;
          });
        }, flashMs + 50);
        prevRef.current = curr;
        return () => clearTimeout(t);
      }
    }
    prevRef.current = curr;
  }, [drivers]);
  return flashes;
}

// Tasarımdan port (variant-minimal): mor gradient daire + içinde stopwatch ikonu.
// d.fastestLap true olduğunda sürücü kodu yanına render edilir.
export function FastestLapDot({ size = 11 }) {
  const purple = '#B93DD6';
  return (
    <div style={{
      width: size, height: size, flexShrink: 0,
      borderRadius: '50%',
      background: `radial-gradient(circle at 30% 30%, ${purple} 0%, #6A1F8A 100%)`,
      boxShadow: `0 0 6px ${purple}cc`,
      display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 10 10">
        <circle cx="5" cy="5.5" r="3.6" fill="none" stroke="#FFF" strokeWidth="0.9" />
        <line x1="5" y1="5.5" x2="5" y2="3" stroke="#FFF" strokeWidth="0.9" strokeLinecap="round" />
        <line x1="5" y1="5.5" x2="6.8" y2="6.5" stroke="#FFF" strokeWidth="0.9" strokeLinecap="round" />
        <rect x="4" y="0.5" width="2" height="1.2" fill="#FFF" rx="0.3" />
      </svg>
    </div>
  );
}

export function PositionDelta({ delta, size = 10 }) {
  if (!delta) {
    return <div style={{ width: size + 4, height: size, flexShrink: 0 }} />;
  }
  const up = delta > 0;
  const color = up ? '#2FE06A' : '#FF3E52';
  return (
    <div style={{
      width: size + 4, height: size, flexShrink: 0,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      animation: 'lbDeltaPulse 2.2s ease-out forwards',
    }}>
      <svg width={size} height={size} viewBox="0 0 10 10">
        {up
          ? <path d="M5 1 L9 8 L5 6 L1 8 Z" fill={color} />
          : <path d="M5 9 L9 2 L5 4 L1 2 Z" fill={color} />}
      </svg>
    </div>
  );
}
