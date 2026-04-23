import VariantClassic from './design/variant-classic.jsx';
import { useSnapshot } from './useSnapshot.js';

export default function App() {
  const { drivers } = useSnapshot();
  // Veri yoksa (oyun menüde / duraklı / backend offline) hiçbir şey render etme
  if (drivers.length === 0) return null;
  return <VariantClassic drivers={drivers} width={305} density="cozy" />;
}
