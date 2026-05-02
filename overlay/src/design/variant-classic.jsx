import { memo } from 'react';
import FlipList from './flip-list.jsx';
import LeaderboardHeader from './header.jsx';
import {
  SectorBars,
  TireCompact,
  ErsCompact,
  PositionDelta,
  FastestLapDot,
  usePositionDeltas,
} from './atoms.jsx';
import { TEAMS } from './constants.js';

const KNOWN_TEAM_IDS = new Set([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);

// PNG'ler çoğunlukla beyaz outline. Mask approach bunları istenen takım
// rengine boyar. Özel durumlar:
//   - Ferrari (1): PNG siyah prancing horse + beyaz/transparent bg →
//     mask bozar (bg opak algılanır), img + invert(1) ile beyaz at
//   - Sauber (9): PNG yeşil dolgulu + K metni → mask kareye dönüşür,
//     img olarak olduğu gibi göster
// Diğerleri: team color mask. Koyu team color'lı takımlar (Red Bull
// #0600EF) için beyaz, gri'ler (Haas #B6BABD) için ikonik kırmızı.
const LOGO_COLOR_BY_TEAM = {
  0: '#FFFFFF',
  2: '#FFFFFF',
  3: '#FFFFFF',
  4: '#FFFFFF',
  5: '#FFFFFF',
  6: '#FFFFFF',
  7: '#E31A2C', // Haas — ikonik kırmızı H
  8: '#FF8700', // McLaren — papaya orange
};

function TeamLogo({ teamId }) {
  if (teamId == null || !KNOWN_TEAM_IDS.has(teamId)) {
    return <div style={{ width: 18, height: 18 }} />;
  }
  if (teamId === 9) {
    return (
      <img src="./teams/9.png" width={18} height={18} alt=""
        style={{ display: 'block', objectFit: 'contain' }} />
    );
  }
  // Ferrari: renkli resmi logo (sarı shield + tricolor + prancing horse + SF)
  // formula1.com CDN'inin logowhite değil logo varyantından indirildi.
  // Mask/filter uygulanmadan direkt render.
  if (teamId === 1) {
    return (
      <img src="./teams/1.png" width={18} height={18} alt=""
        style={{ display: 'block', objectFit: 'contain' }} />
    );
  }
  const color = LOGO_COLOR_BY_TEAM[teamId] || '#FFFFFF';
  return (
    <div style={{
      width: 18, height: 18, backgroundColor: color,
      maskImage: `url(./teams/${teamId}.png)`,
      maskRepeat: 'no-repeat', maskSize: 'contain', maskPosition: 'center',
      WebkitMaskImage: `url(./teams/${teamId}.png)`,
      WebkitMaskRepeat: 'no-repeat', WebkitMaskSize: 'contain', WebkitMaskPosition: 'center',
    }} />
  );
}

// "M:SS.mmm" / "SS.mmm" — F1 broadcast tarzı
function formatLapTime(ms) {
  if (!ms || ms <= 0) return '—';
  const totalSec = ms / 1000;
  if (totalSec < 60) return totalSec.toFixed(3);
  const m = Math.floor(totalSec / 60);
  const s = totalSec - m * 60;
  return `${m}:${s.toFixed(3).padStart(6, '0')}`;
}

export default function VariantClassic({
  drivers,
  session,
  lapTimeMode = false,
  inPit = false,
  width = 360,
  density = 'cozy',
}) {
  const rowH = density === 'compact' ? 26 : 30;
  const fontSize = density === 'compact' ? 13 : 14;
  const deltas = usePositionDeltas(drivers);
  // Yarış-dışı (pratik/sıralama) + oyuncu pite girdiyse leaderboard kapanır,
  // sadece header kalır. Yarışta pit gizlenmesi yok.
  const collapsed = lapTimeMode && inPit;

  return (
    <div style={{
      width,
      background: 'rgba(10, 10, 14, 0.92)',
      fontFamily: "'Rajdhani', 'Oswald', sans-serif",
      color: '#ECECEC',
      borderRadius: 4,
      overflow: 'hidden',
    }}>
      <LeaderboardHeader session={session} tone="classic" inPit={inPit && lapTimeMode} />
      {!collapsed && (
        <div style={{ padding: '4px 0' }}>
          <FlipList keyFn={d => d.code} items={drivers}>
            {(d) => {
              const flash = deltas[d.code];
              return (
                <Row
                  driver={d}
                  rowH={rowH}
                  fontSize={fontSize}
                  flashDelta={flash ? flash.delta : 0}
                  flashAt={flash ? flash.at : null}
                  lapTimeMode={lapTimeMode}
                />
              );
            }}
          </FlipList>
        </div>
      )}
    </div>
  );
}

const Row = memo(function Row({ driver: d, rowH, fontSize, flashDelta, flashAt, lapTimeMode }) {
  const teamColor = d.teamColor || TEAMS[d.team]?.color || '#808080';
  const isPlayer = d.isPlayer;
  // Yarış-dışı modda gap yerine canlı tur süresi
  const trailingText = lapTimeMode
    ? formatLapTime(d.currentLapTimeMs)
    : (d.gap === 'LEADER' ? 'INTERVAL' : d.gap);
  const trailingColor = lapTimeMode
    ? '#ECECEC'
    : (d.gap === 'LEADER' ? '#F6C416' : '#ECECEC');
  return (
    <div style={{
      height: rowH,
      display: 'grid',
      gridTemplateColumns: '12px 4px 22px 18px 50px 1fr auto auto auto',
      alignItems: 'center',
      gap: 6,
      padding: '0 8px 0 0',
      background: isPlayer
        ? 'linear-gradient(90deg, rgba(225,29,46,0.35) 0%, rgba(225,29,46,0.08) 100%)'
        : 'transparent',
      borderBottom: '1px solid rgba(255,255,255,0.03)',
      position: 'relative',
      contain: 'layout paint',
    }}>
      <PositionDelta key={flashAt || 'none-' + d.code} delta={flashDelta} size={10} />
      <div style={{ width: 4, height: '70%', background: teamColor, borderRadius: 1 }} />
      <div style={{
        fontSize: fontSize + 2, fontWeight: 700, textAlign: 'center',
        color: isPlayer ? '#FFF' : '#ECECEC',
        fontVariantNumeric: 'tabular-nums',
      }}>{d.pos}</div>
      <TeamLogo teamId={d.teamId} />
      <div style={{
        fontSize, fontWeight: 700, letterSpacing: 1.2,
        color: isPlayer ? '#FFF' : '#ECECEC',
        display: 'flex', alignItems: 'center', gap: 4,
      }}>
        {d.code}
        {d.fastestLap && <FastestLapDot size={11} />}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
        <SectorBars sectors={d.sectors} height={10} width={6} gap={2} />
      </div>
      <div style={{
        fontSize: fontSize - 1, fontWeight: 700, letterSpacing: 0.5,
        color: trailingColor,
        fontVariantNumeric: 'tabular-nums',
        minWidth: 56, textAlign: 'right',
      }}>{trailingText}</div>
      <ErsCompact ers={d.ers} mode={d.ersMode} />
      <TireCompact compound={d.compound} wear={d.wear} laps={d.laps} />
    </div>
  );
});
