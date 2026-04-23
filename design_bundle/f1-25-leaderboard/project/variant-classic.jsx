// VARIANT 1 — Classic Broadcast
// Faithful to the reference structure but cleaner: dark rows, team color on
// the left edge, crest + code, sector bars, gap, tire.

function VariantClassic({ drivers, width = 360, density = 'cozy' }) {
  const rowH = density === 'compact' ? 26 : 30;
  const fontSize = density === 'compact' ? 13 : 14;
  const deltas = window.usePositionDeltas(drivers);

  return (
    <div style={{
      width,
      background: 'rgba(10, 10, 14, 0.86)',
      backdropFilter: 'blur(6px)',
      WebkitBackdropFilter: 'blur(6px)',
      fontFamily: "'Rajdhani', 'Oswald', sans-serif",
      color: '#ECECEC',
      borderRadius: 4,
      overflow: 'hidden',
      boxShadow: '0 8px 40px rgba(0,0,0,.5)',
      padding: '4px 0',
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
              gridTemplateColumns: '14px 4px 26px 18px 42px 1fr auto auto auto',
              alignItems: 'center',
              gap: 8,
              padding: '0 8px 0 0',
              background: isPlayer ? 'linear-gradient(90deg, rgba(225,29,46,0.35) 0%, rgba(225,29,46,0.08) 100%)' : 'transparent',
              borderBottom: '1px solid rgba(255,255,255,0.03)',
              position: 'relative',
            }}>
              {/* delta arrow */}
              <window.PositionDelta key={flash ? flash.at : 'none-' + d.code} delta={flash ? flash.delta : 0} size={10} />
              {/* team-color edge */}
              <div style={{ width: 4, height: '70%', background: t.color, borderRadius: 1 }} />
              {/* position */}
              <div style={{
                fontSize: fontSize + 2, fontWeight: 700, textAlign: 'center',
                color: isPlayer ? '#FFF' : '#ECECEC',
                fontVariantNumeric: 'tabular-nums',
              }}>{d.pos}</div>
              {/* crest */}
              <window.TeamCrest team={d.team} size={16} />
              {/* code */}
              <div style={{
                fontSize, fontWeight: 700, letterSpacing: 1.2,
                color: isPlayer ? '#FFF' : '#ECECEC',
              }}>{d.code}</div>
              {/* sectors (fills remaining) */}
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <window.SectorBars sectors={d.sectors} height={10} width={6} gap={2} />
              </div>
              {/* gap */}
              <div style={{
                fontSize: fontSize - 1, fontWeight: 700, letterSpacing: 0.5,
                color: d.gap === 'LEADER' ? '#F6C416' : '#ECECEC',
                fontVariantNumeric: 'tabular-nums',
                minWidth: 48, textAlign: 'right',
              }}>{d.gap === 'LEADER' ? 'INTERVAL' : d.gap}</div>
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

window.VariantClassic = VariantClassic;
