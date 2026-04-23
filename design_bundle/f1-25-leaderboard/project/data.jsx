// Original fictional F1-style teams so no real branding is recreated.
// Your Python UDP listener can swap in real team metadata from telemetry.

const TEAMS = {
  APX: { name: 'Apex Dynamics',   color: '#E4002B', dark: '#8A0019' },
  VLK: { name: 'Volkeni Motors',  color: '#00D7B8', dark: '#00786A' },
  NRD: { name: 'Nordica Racing',  color: '#C0C6CC', dark: '#5A6168' },
  KRN: { name: 'Kerenza GP',      color: '#FFB800', dark: '#8A6400' },
  ORB: { name: 'Orbita Works',    color: '#FF6B1A', dark: '#8A3A0E' },
  SLC: { name: 'Silicora',        color: '#6A5AE0', dark: '#3A2F8C' },
  TRN: { name: 'Tornado Racing',  color: '#1E5BFF', dark: '#0D2F8A' },
  VRT: { name: 'Veritas Auto',    color: '#00B84A', dark: '#006A2B' },
  MRD: { name: 'Meridian F1',     color: '#D946EF', dark: '#7A1F8A' },
  HLX: { name: 'Helix Engineering', color: '#F5F5F0', dark: '#8A8A85' },
};

// sector: 0=none, 1=personal-best (yellow), 2=overall-best (purple), 3=green (improving)
// compound: S=soft(red), M=medium(yellow), H=hard(white), I=intermediate(green), W=wet(blue)
// ers: battery 0-100 (%), mode N=none, M=medium, O=overtake, H=hotlap
const DRIVERS = [
  { pos: 1,  code: 'VRS', name: 'Varsen',     team: 'APX', sectors: [2,2,0], gap: 'LEADER', compound: 'S', wear: 18, laps: 8,  ers: 72, ersMode: 'M' },
  { pos: 2,  code: 'BLK', name: 'Blake',      team: 'VLK', sectors: [1,0,0], gap: '+1.563', compound: 'S', wear: 22, laps: 9,  ers: 64, ersMode: 'O' },
  { pos: 3,  code: 'ROH', name: 'Rohner',     team: 'NRD', sectors: [0,1,0], gap: '+0.101', compound: 'M', wear: 35, laps: 14, ers: 88, ersMode: 'M' },
  { pos: 4,  code: 'KAI', name: 'Kaiser',     team: 'VLK', sectors: [3,0,0], gap: '+0.840', compound: 'S', wear: 24, laps: 9,  ers: 41, ersMode: 'M' },
  { pos: 5,  code: 'VEN', name: 'Vento',      team: 'ORB', sectors: [0,0,2], gap: '+0.151', compound: 'M', wear: 41, laps: 15, ers: 23, ersMode: 'N' },
  { pos: 6,  code: 'UYS', name: 'Uysal',      team: 'APX', sectors: [0,0,0], gap: '+0.792', compound: 'S', wear: 28, laps: 10, ers: 55, ersMode: 'O', isPlayer: true },
  { pos: 7,  code: 'HAM', name: 'Hamer',      team: 'TRN', sectors: [1,1,0], gap: '+0.455', compound: 'M', wear: 46, laps: 16, ers: 78, ersMode: 'M' },
  { pos: 8,  code: 'ANT', name: 'Antoli',     team: 'NRD', sectors: [0,0,1], gap: '+0.708', compound: 'H', wear: 12, laps: 5,  ers: 92, ersMode: 'H' },
  { pos: 9,  code: 'TSU', name: 'Tsunoba',    team: 'KRN', sectors: [0,0,0], gap: '+0.473', compound: 'M', wear: 52, laps: 18, ers: 34, ersMode: 'M' },
  { pos: 10, code: 'HLM', name: 'Holman',     team: 'VRT', sectors: [3,0,0], gap: '+0.440', compound: 'M', wear: 38, laps: 13, ers: 60, ersMode: 'M' },
  { pos: 11, code: 'GAS', name: 'Gaston',     team: 'SLC', sectors: [0,1,0], gap: '+0.355', compound: 'S', wear: 15, laps: 6,  ers: 81, ersMode: 'O' },
  { pos: 12, code: 'NOR', name: 'Norden',     team: 'ORB', sectors: [0,0,3], gap: '+0.455', compound: 'M', wear: 44, laps: 16, ers: 18, ersMode: 'N' },
  { pos: 13, code: 'BEA', name: 'Beaumont',   team: 'KRN', sectors: [0,0,0], gap: '+0.911', compound: 'H', wear: 8,  laps: 3,  ers: 96, ersMode: 'M' },
  { pos: 14, code: 'OCO', name: 'Okonma',     team: 'MRD', sectors: [1,0,0], gap: '+0.203', compound: 'S', wear: 20, laps: 8,  ers: 47, ersMode: 'M' },
  { pos: 15, code: 'PIR', name: 'Piraud',     team: 'ORB', sectors: [0,0,0], gap: '+0.422', compound: 'M', wear: 49, laps: 17, ers: 29, ersMode: 'M' },
  { pos: 16, code: 'COL', name: 'Colton',     team: 'VRT', sectors: [0,3,0], gap: '+0.506', compound: 'M', wear: 43, laps: 15, ers: 66, ersMode: 'O' },
  { pos: 17, code: 'ARO', name: 'Aronov',     team: 'HLX', sectors: [0,0,0], gap: '+0.894', compound: 'H', wear: 6,  laps: 2,  ers: 85, ersMode: 'M' },
  { pos: 18, code: 'STR', name: 'Strand',     team: 'MRD', sectors: [0,0,0], gap: '+0.388', compound: 'S', wear: 31, laps: 11, ers: 52, ersMode: 'M' },
  { pos: 19, code: 'HDA', name: 'Hadari',     team: 'HLX', sectors: [0,1,0], gap: '+0.286', compound: 'M', wear: 55, laps: 19, ers: 12, ersMode: 'N' },
  { pos: 20, code: 'BOR', name: 'Bordeleau',  team: 'SLC', sectors: [0,0,0], gap: '+0.557', compound: 'H', wear: 14, laps: 6,  ers: 74, ersMode: 'M' },
];

// ERS mode colors — cyan family (keeps it distinct from sector greens/yellows)
const ERS_MODE_COLORS = {
  N: '#5A6168',  // none / off — gray
  M: '#2AD9E6',  // medium — cyan
  O: '#FFB800',  // overtake — amber (more aggressive)
  H: '#FF2E6A',  // hotlap — hot pink/red
};
const ERS_MODE_LABELS = {
  N: 'OFF', M: 'MED', O: 'OVT', H: 'HOT',
};

const COMPOUND_COLORS = {
  S: '#E11D2E',  // soft - red
  M: '#F6C416',  // medium - yellow
  H: '#ECECEC',  // hard - white
  I: '#2FB344',  // inter - green
  W: '#2A8BF2',  // wet - blue
};

const SECTOR_COLORS = {
  0: '#3A3A40', // gray / none
  1: '#F6C416', // personal best - yellow
  2: '#B93DD6', // overall best - purple
  3: '#2FB344', // green / improving
};

Object.assign(window, { TEAMS, DRIVERS, COMPOUND_COLORS, SECTOR_COLORS, ERS_MODE_COLORS, ERS_MODE_LABELS });
