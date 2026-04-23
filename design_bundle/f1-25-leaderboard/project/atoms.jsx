// Shared atoms used across all three leaderboard variants.

// Team "crest" — NOT real F1 logos. A simple geometric glyph per team,
// filled with the team color. Python side can swap in real logo images.
function TeamCrest({ team, size = 16 }) {
  const t = window.TEAMS[team];
  if (!t) return null;
  const glyphs = {
    APX: <path d="M8 2 L14 14 L2 14 Z" />,                     // triangle
    VLK: <path d="M2 8 L8 2 L14 8 L8 14 Z" />,                  // diamond
    NRD: <path d="M2 4 L14 4 L14 12 L2 12 Z M2 8 L14 8" stroke="#0b0b0f" strokeWidth="1.2" fill="none" />,
    KRN: <path d="M8 1.5 L9.8 6 L14.5 6 L10.7 9 L12.2 13.5 L8 10.8 L3.8 13.5 L5.3 9 L1.5 6 L6.2 6 Z" />,
    ORB: <g><circle cx="8" cy="8" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" /><circle cx="8" cy="8" r="1.6" /></g>,
    SLC: <path d="M3 3 H13 V6 L9 8 L13 10 V13 H3 V10 L7 8 L3 6 Z" />,
    TRN: <path d="M2 13 Q5 3 14 3 Q11 8 14 13 Q9 10 2 13 Z" />, // swoosh
    VRT: <path d="M2 3 H14 L9 13 H7 Z" />,                      // chevron
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

// Three thin sector bars (user asked for 3 ince bar variant).
function SectorBars({ sectors, height = 10, width = 7, gap = 3 }) {
  return (
    <div style={{ display: 'flex', gap: `${gap}px`, alignItems: 'center' }}>
      {sectors.map((s, i) => (
        <div
          key={i}
          style={{
            width: `${width}px`,
            height: `${height}px`,
            borderRadius: '1px',
            background: window.SECTOR_COLORS[s],
            boxShadow: s > 0 ? `0 0 4px ${window.SECTOR_COLORS[s]}66` : 'none',
            transition: 'background 180ms',
          }}
        />
      ))}
    </div>
  );
}

// Tire: compound-colored ring, wear% shown by arc length, laps in center.
function TireIndicator({ compound, wear, laps, size = 22 }) {
  const color = window.COMPOUND_COLORS[compound];
  const r = size / 2 - 2;
  const cx = size / 2;
  const cy = size / 2;
  const circ = 2 * Math.PI * r;
  // wear is "used %". Arc shows remaining.
  const remaining = Math.max(0, 100 - wear) / 100;
  const dash = circ * remaining;
  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ display: 'block' }}>
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#2A2A30" strokeWidth="2" />
        <circle
          cx={cx}
          cy={cy}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="2.2"
          strokeDasharray={`${dash} ${circ}`}
          strokeLinecap="round"
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dasharray 220ms' }}
        />
        <text
          x={cx}
          y={cy + 3}
          textAnchor="middle"
          fontSize="9"
          fontWeight="700"
          fill={color}
          fontFamily="'Rajdhani', sans-serif"
        >
          {compound}
        </text>
      </svg>
      <div
        style={{
          position: 'absolute',
          top: '100%',
          left: '50%',
          transform: 'translate(-50%, -30%)',
          fontSize: 8,
          color: '#9AA0A6',
          fontWeight: 700,
          fontFamily: "'Rajdhani', sans-serif",
          letterSpacing: 0.3,
          pointerEvents: 'none',
          display: 'none',
        }}
      >
        L{laps}
      </div>
    </div>
  );
}

// Inline tire with lap-count badge next to it (compact layout).
function TireCompact({ compound, wear, laps }) {
  const color = window.COMPOUND_COLORS[compound];
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

// ERS — battery % as a vertical/horizontal fill, mode label badge beside.
// Compact horizontal version used inline in rows.
function ErsCompact({ ers, mode }) {
  const modeColor = window.ERS_MODE_COLORS[mode] || '#5A6168';
  const label = window.ERS_MODE_LABELS[mode] || 'OFF';
  const pct = Math.max(0, Math.min(100, ers));
  // Low battery warning color
  const barColor = pct < 20 ? '#E11D2E' : pct < 40 ? '#F6C416' : '#2AD9E6';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
      {/* battery bar */}
      <div style={{
        width: 22, height: 10,
        background: '#1A1A20',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: 1,
        position: 'relative',
        padding: 1,
        boxSizing: 'border-box',
      }}>
        <div style={{
          width: `${pct}%`, height: '100%',
          background: barColor,
          transition: 'width 220ms, background 220ms',
          boxShadow: pct > 80 ? `0 0 4px ${barColor}` : 'none',
        }} />
        {/* battery nub */}
        <div style={{
          position: 'absolute', right: -2, top: 2, bottom: 2,
          width: 2, background: 'rgba(255,255,255,0.15)',
          borderRadius: 1,
        }} />
      </div>
      {/* mode label */}
      <span style={{
        fontSize: 9, fontWeight: 800, letterSpacing: 0.6,
        color: modeColor,
        fontFamily: "'Rajdhani', sans-serif",
        minWidth: 22, textAlign: 'left',
        textShadow: mode === 'H' || mode === 'O' ? `0 0 6px ${modeColor}88` : 'none',
      }}>{label}</span>
    </div>
  );
}

// Minimal version: just a thin bar with mode-colored fill — no label.
function ErsBar({ ers, mode, width = 24, height = 3 }) {
  const modeColor = window.ERS_MODE_COLORS[mode] || '#5A6168';
  const pct = Math.max(0, Math.min(100, ers));
  return (
    <div style={{
      width, height,
      background: '#1A1A20',
      borderRadius: 1,
      overflow: 'hidden',
    }}>
      <div style={{
        width: `${pct}%`, height: '100%',
        background: modeColor,
        transition: 'width 220ms, background 220ms',
      }} />
    </div>
  );
}

// Track position changes and return a map of code -> delta (old - new).
// Positive = gained positions (went up), negative = lost.
// The delta "flashes" for flashMs then clears.
function usePositionDeltas(drivers, flashMs = 2200) {
  const prevRef = React.useRef(null);
  const [flashes, setFlashes] = React.useState({});
  React.useEffect(() => {
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

// Small up/down arrow rendered in a fixed-width slot. Renders nothing when
// delta is 0/undefined — slot still takes space so layout doesn't shift.
function PositionDelta({ delta, size = 10 }) {
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
      <svg width={size} height={size} viewBox="0 0 10 10" style={{
        filter: `drop-shadow(0 0 3px ${color}aa)`,
      }}>
        {up
          ? <path d="M5 1 L9 8 L5 6 L1 8 Z" fill={color} />
          : <path d="M5 9 L9 2 L5 4 L1 2 Z" fill={color} />}
      </svg>
    </div>
  );
}

Object.assign(window, { TeamCrest, SectorBars, TireIndicator, TireCompact, ErsCompact, ErsBar, usePositionDeltas, PositionDelta });
