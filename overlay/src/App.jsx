import VariantClassic from './design/variant-classic.jsx';
import { useSnapshot } from './useSnapshot.js';

export default function App() {
  const { drivers, session, connected } = useSnapshot();
  if (drivers.length === 0) {
    // Dev modunda overlay'in canlı olduğunu gösteren tanı rozeti.
    // Üretimde (paketlenmiş build) görünmez kalır.
    if (import.meta.env.DEV) {
      return (
        <div style={{
          position: 'fixed', top: 8, left: 8,
          padding: '6px 10px', borderRadius: 4,
          background: 'rgba(0,0,0,0.78)', color: '#fff',
          font: '12px ui-monospace, Menlo, Consolas, monospace',
          pointerEvents: 'none', userSelect: 'none',
        }}>
          overlay ready · WS {connected ? 'connected' : 'disconnected'} · drivers 0
        </div>
      );
    }
    return null;
  }
  const player = drivers.find(d => d.isPlayer);
  // Yarış-dışı modlar: gap kolonu canlı tur süresine çevrilir, pite girilince
  // tablo gizlenir. Pratik + sıralama (sprint sıralama dahil) bu kategoride.
  const lapTimeMode = (
    session?.type === 'PRATİK'
    || session?.type === 'SIRALAMA'
    || session?.type === 'SPRINT SIRALAMA'
  );
  const inPit = !!(player && player.pitStatus > 0);
  return (
    <VariantClassic
      drivers={drivers}
      session={session}
      lapTimeMode={lapTimeMode}
      inPit={inPit}
      width={305}
      density="cozy"
    />
  );
}
