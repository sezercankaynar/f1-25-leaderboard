// Tasarımdan port (header.jsx). Placeholder HeaderMark yerine resmi F1 logosu
// (./f1-logo.svg, scripts/download_f1_logo.py ile çekilir) kullanılır.

function F1Logo({ height = 18 }) {
  // Logo'nun doğal en/boy oranı ~2:1 — height ver, width auto.
  return (
    <img
      src="./f1-logo.svg"
      alt="F1"
      style={{ height, width: 'auto', display: 'block', flexShrink: 0 }}
      draggable={false}
    />
  );
}

function WeatherIcon({ weather, size = 14 }) {
  if (weather === 'dry') {
    return (
      <svg width={size} height={size} viewBox="0 0 14 14">
        <circle cx="7" cy="7" r="2.6" fill="#F6C416" />
        <g stroke="#F6C416" strokeWidth="1.2" strokeLinecap="round">
          <line x1="7" y1="0.8" x2="7" y2="2.4" />
          <line x1="7" y1="11.6" x2="7" y2="13.2" />
          <line x1="0.8" y1="7" x2="2.4" y2="7" />
          <line x1="11.6" y1="7" x2="13.2" y2="7" />
          <line x1="2.4" y1="2.4" x2="3.6" y2="3.6" />
          <line x1="10.4" y1="10.4" x2="11.6" y2="11.6" />
          <line x1="2.4" y1="11.6" x2="3.6" y2="10.4" />
          <line x1="10.4" y1="3.6" x2="11.6" y2="2.4" />
        </g>
      </svg>
    );
  }
  if (weather === 'cloudy') {
    return (
      <svg width={size} height={size} viewBox="0 0 14 14">
        <path d="M3.5 9.5 Q1 9.5 1 7 Q1 5 3.5 5 Q3.5 2.5 6 2.5 Q9 2.5 9.5 5 Q12 5 12 7.5 Q12 9.5 9.5 9.5 Z" fill="#9AA0A6" />
      </svg>
    );
  }
  return (
    <svg width={size} height={size} viewBox="0 0 14 14">
      <path d="M3.5 7 Q1 7 1 5 Q1 3 3.5 3 Q3.5 1 6 1 Q9 1 9.5 3 Q12 3 12 5.5 Q12 7 9.5 7 Z" fill="#9AA0A6" />
      <line x1="4"   y1="9"  x2="3"   y2="13" stroke="#2A8BF2" strokeWidth="1.1" strokeLinecap="round" />
      <line x1="6.8" y1="9"  x2="5.8" y2="13" stroke="#2A8BF2" strokeWidth="1.1" strokeLinecap="round" />
      <line x1="9.6" y1="9"  x2="8.6" y2="13" stroke="#2A8BF2" strokeWidth="1.1" strokeLinecap="round" />
    </svg>
  );
}

function lapStyle(big) {
  return {
    fontSize: big ? 17 : 15,
    fontWeight: 800,
    color: '#FFFFFF',
    fontVariantNumeric: 'tabular-nums',
    fontFamily: big ? "'Oswald', sans-serif" : "'Rajdhani', sans-serif",
    letterSpacing: 0.5,
    display: 'inline-flex',
    alignItems: 'baseline',
  };
}

function ConditionCell({ label, value, icon, accent, centered, alignRight }) {
  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      alignItems: alignRight ? 'flex-end' : centered ? 'center' : 'flex-start',
      gap: 1,
    }}>
      <span style={{
        fontSize: 9, fontWeight: 700, letterSpacing: 1.2,
        color: '#7A8088', textTransform: 'uppercase',
      }}>{label}</span>
      <span style={{
        display: 'flex', alignItems: 'center', gap: 4,
        justifyContent: alignRight ? 'flex-end' : centered ? 'center' : 'flex-start',
        fontSize: 13, fontWeight: 700,
        color: accent || '#ECECEC',
        fontVariantNumeric: 'tabular-nums',
      }}>
        {icon}
        {value}
      </span>
    </div>
  );
}

function Divider() {
  return <div style={{ width: 1, height: 22, background: 'rgba(255,255,255,0.06)', justifySelf: 'center' }} />;
}

export default function LeaderboardHeader({ session, tone = 'classic', inPit = false }) {
  const big = tone === 'bold';
  const minimal = tone === 'minimal';

  let lapInfo;
  const t = (session?.type || '').toUpperCase();
  if (inPit) {
    // Pit modu: lap/timer yerine kırmızı PİT rozeti
    lapInfo = (
      <span style={{
        fontSize: big ? 13 : 12,
        fontWeight: 800,
        letterSpacing: 1.6,
        color: '#FFFFFF',
        background: 'rgba(225, 29, 46, 0.85)',
        padding: '3px 10px',
        borderRadius: 2,
        textTransform: 'uppercase',
        fontFamily: "'Rajdhani', sans-serif",
      }}>PİT</span>
    );
  } else if (t === 'YARIŞ' || t === 'YARIS' || t === 'RACE') {
    lapInfo = (
      <span style={lapStyle(big)}>
        <span style={{ color: '#9AA0A6', fontWeight: 600, fontSize: '0.65em', letterSpacing: 1.4, marginRight: 5 }}>TUR</span>
        {session.lap}<span style={{ color: '#5A6168', fontWeight: 600 }}>/{session.totalLaps}</span>
      </span>
    );
  } else if (session?.timeLeft) {
    lapInfo = <span style={lapStyle(big)}>{session.timeLeft}</span>;
  } else {
    lapInfo = (
      <span style={{ ...lapStyle(big), color: '#9AA0A6', fontSize: big ? 13 : 12, letterSpacing: 1.4 }}>
        — — —
      </span>
    );
  }

  return (
    <div style={{ fontFamily: "'Rajdhani', sans-serif", color: '#ECECEC' }}>
      {/* TOP: logo + session type + lap */}
      <div style={{
        padding: minimal ? '8px 12px' : '10px 12px 9px',
        background: 'linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.01))',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 8,
        }}>
          <F1Logo height={big ? 20 : 18} />
          <span style={{
            fontSize: big ? 12 : 11,
            fontWeight: 700,
            letterSpacing: 1.8,
            color: '#ECECEC',
            textTransform: 'uppercase',
            fontFamily: big ? "'Oswald', 'Rajdhani', sans-serif" : "'Rajdhani', sans-serif",
            padding: '2px 8px',
            background: 'rgba(255,255,255,0.06)',
            borderRadius: 2,
          }}>{session?.type || '—'}</span>
          <span style={{ display: 'flex', alignItems: 'baseline' }}>{lapInfo}</span>
        </div>
      </div>

      {/* BOTTOM: pist/hava sıcaklığı + yağış */}
      <div style={{
        padding: minimal ? '6px 12px 8px' : '7px 12px 9px',
        background: 'rgba(0,0,0,0.25)',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
        display: 'grid',
        gridTemplateColumns: '1fr 1px 1fr 1px 1fr',
        gap: 6,
        alignItems: 'center',
      }}>
        <ConditionCell label="PİST" value={`${session?.trackTemp ?? 0}°`} />
        <Divider />
        <ConditionCell label="HAVA" value={`${session?.airTemp ?? 0}°`} centered />
        <Divider />
        <ConditionCell
          label="YAĞIŞ"
          value={`${session?.rainChance ?? 0}%`}
          icon={<WeatherIcon weather={session?.weather || 'dry'} size={12} />}
          accent={(session?.rainChance ?? 0) > 40 ? '#2A8BF2' : null}
          alignRight
        />
      </div>
    </div>
  );
}
