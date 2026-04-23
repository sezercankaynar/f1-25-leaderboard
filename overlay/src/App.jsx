import VariantClassic from './design/variant-classic.jsx';
import { useSnapshot } from './useSnapshot.js';

export default function App() {
  const { connected, drivers } = useSnapshot();

  if (drivers.length === 0) {
    return (
      <div style={{
        padding: '12px 18px',
        background: 'rgba(10,10,14,0.92)',
        borderRadius: 4,
        color: connected ? '#9AA0A6' : '#E11D2E',
        fontSize: 13,
        fontWeight: 700,
        letterSpacing: 1.5,
        textTransform: 'uppercase',
        fontFamily: "'Rajdhani', sans-serif",
      }}>
        {connected ? 'Waiting for UDP…' : 'Backend offline'}
      </div>
    );
  }

  return <VariantClassic drivers={drivers} width={305} density="cozy" />;
}
