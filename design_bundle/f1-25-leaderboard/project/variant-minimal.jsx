// VARIANT 3 — Minimal Split
// Dark, very tight, tabular. Team color is only a hairline on the left.
// Typography-led — inspired by motorsport TV timing towers but ultra-clean.

function VariantMinimal({ drivers, width = 360, density = 'cozy' }) {
  const rowH = density === 'compact' ? 28 : 32;
  const deltas = window.usePositionDeltas(drivers);

  return (
    <div style={{
      width,
      background: 'rgba(14, 14, 18, 0.82)',
      backdropFilter: 'blur(8px)',
      WebkitBackdropFilter: 'blur(8px)',
      fontFamily: "'Rajdhani', sans-serif",
      color: '#ECECEC',
      borderRadius: 6,
      overflow: 'hidden',
      boxShadow: '0 8px 40px rgba(0,0,0,.5)',
      border: '1px solid rgba(255,255,255,0.06)',
    }}>
      <FlipList keyFn={d => d.code} items={drivers}>
        {(d, i) => {
          const t = window.TEAMS[d.team];
          const isPlayer = d.isPlayer;
          const isLast = i === drivers.length - 1;
          const flash = deltas[d.code];
          return (
            <div style={{
              height: rowH,
              display: 'grid',
              gridTemplateColumns: '14px 2px 22px 16px 40px 1fr auto auto',
              alignItems: 'center',
              gap: 8,
              paddingRight: 10,
              background: isPlayer ? 'rgba(225, 29, 46, 0.22)' : 'transparent',
              borderBottom: isLast ? 'none' : '1px solid rgba(255,255,255,0.035)',
              position: 'relative',
            }}>
              {/* delta arrow */}
              <window.PositionDelta key={flash ? flash.at : 'none-' + d.code} delta={flash ? flash.delta : 0} size={9} />
              {/* team hairline */}
              <div style={{ width: 2, height: '100%', background: t.color }} />
              {/* position */}
              <div style={{
                fontSize: 13, fontWeight: 600, textAlign: 'center',
                color: '#9AA0A6',
                fontVariantNumeric: 'tabular-nums',
              }}>{d.pos}</div>
              {/* crest */}
              <window.TeamCrest team={d.team} size={14} />
              {/* code */}
              <div style={{
                fontSize: 13, fontWeight: 700, letterSpacing: 1.2,
                color: isPlayer ? '#FFF' : '#ECECEC',
              }}>{d.code}</div>
              {/* sectors + ERS bar stacked */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 2, justifyContent: 'center' }}>
                <window.SectorBars sectors={d.sectors} height={6} width={6} gap={2} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                  <window.ErsBar ers={d.ers} mode={d.ersMode} width={22} height={3} />
                  <span style={{
                    fontSize: 8, fontWeight: 800, letterSpacing: 0.4,
                    color: window.ERS_MODE_COLORS[d.ersMode],
                    fontFamily: "'Rajdhani', sans-serif",
                  }}>{window.ERS_MODE_LABELS[d.ersMode]}</span>
                </div>
              </div>
              {/* gap */}
              <div style={{
                fontSize: 12, fontWeight: 600, letterSpacing: 0.3,
                color: d.gap === 'LEADER' ? '#F6C416' : '#CFCFCF',
                fontVariantNumeric: 'tabular-nums',
                minWidth: 48, textAlign: 'right',
                fontFeatureSettings: '"tnum"',
              }}>{d.gap === 'LEADER' ? '—' : d.gap}</div>
              {/* tire */}
              <window.TireCompact compound={d.compound} wear={d.wear} laps={d.laps} />
            </div>
          );
        }}
      </FlipList>
    </div>
  );
}

window.VariantMinimal = VariantMinimal;
