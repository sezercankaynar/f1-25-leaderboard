// VARIANT 2 — Bold Bar
// Team color as a full-row accent that wraps around position number.
// Chunky typography, higher visual weight, very "broadcast TV".

function VariantBoldBar({ drivers, width = 360, density = 'cozy' }) {
  const rowH = density === 'compact' ? 30 : 34;
  const deltas = window.usePositionDeltas(drivers);

  return (
    <div style={{
      width,
      background: 'rgba(8, 8, 12, 0.88)',
      backdropFilter: 'blur(6px)',
      WebkitBackdropFilter: 'blur(6px)',
      fontFamily: "'Rajdhani', 'Oswald', sans-serif",
      color: '#ECECEC',
      borderRadius: 2,
      overflow: 'hidden',
      boxShadow: '0 8px 40px rgba(0,0,0,.55)',
      padding: '3px',
      display: 'flex', flexDirection: 'column', gap: 2,
    }}>
      <FlipList keyFn={d => d.code} items={drivers}>
        {(d) => {
          const t = window.TEAMS[d.team];
          const isPlayer = d.isPlayer;
          const flash = deltas[d.code];
          return (
            <div style={{
              height: rowH,
              display: 'grid',
              gridTemplateColumns: `14px ${rowH}px 20px 48px 1fr auto auto auto`,
              alignItems: 'center',
              gap: 8,
              padding: '0 8px 0 0',
              background: isPlayer
                ? 'linear-gradient(90deg, #C81028 0%, rgba(200,16,40,0.15) 70%, rgba(200,16,40,0) 100%)'
                : 'linear-gradient(90deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01))',
              position: 'relative',
              overflow: 'hidden',
            }}>
              {/* delta arrow */}
              <window.PositionDelta key={flash ? flash.at : 'none-' + d.code} delta={flash ? flash.delta : 0} size={10} />
              {/* position block with team-color bottom stripe */}
              <div style={{
                height: '100%',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                background: isPlayer ? 'transparent' : '#0b0b0f',
                position: 'relative',
                fontSize: 18, fontWeight: 800,
                fontVariantNumeric: 'tabular-nums',
                color: '#FFF',
                fontFamily: "'Oswald', 'Rajdhani', sans-serif",
              }}>
                {d.pos}
                <div style={{
                  position: 'absolute', left: 4, right: 4, bottom: 3, height: 2,
                  background: t.color, borderRadius: 1,
                }} />
              </div>
              {/* crest */}
              <window.TeamCrest team={d.team} size={18} />
              {/* code */}
              <div style={{
                fontSize: 15, fontWeight: 700, letterSpacing: 1.4,
                color: '#FFF',
                fontFamily: "'Oswald', 'Rajdhani', sans-serif",
              }}>{d.code}</div>
              {/* sectors */}
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <window.SectorBars sectors={d.sectors} height={12} width={7} gap={2} />
              </div>
              {/* gap */}
              <div style={{
                fontSize: 13, fontWeight: 700, letterSpacing: 0.4,
                color: d.gap === 'LEADER' ? '#F6C416' : '#ECECEC',
                fontVariantNumeric: 'tabular-nums',
                minWidth: 52, textAlign: 'right',
                fontFamily: "'Rajdhani', sans-serif",
              }}>{d.gap === 'LEADER' ? 'LEADER' : d.gap}</div>
              {/* ERS */}
              <window.ErsCompact ers={d.ers} mode={d.ersMode} />
              {/* tire */}
              <window.TireCompact compound={d.compound} wear={d.wear} laps={d.laps} />
            </div>
          );
        }}
      </FlipList>
    </div>
  );
}

window.VariantBoldBar = VariantBoldBar;
