export const colors = {
  // Field — navy scale
  field900: '#0a1322',
  field800: '#0e1a30',
  field700: '#142342',
  field600: '#1b2d52',
  field500: '#243a66',

  // Strokes
  stroke:  '#25395f',
  stroke2: '#36507f',
  hairline: 'rgba(212, 162, 74, 0.28)',

  // Brand
  crimson:   '#a8243a',
  crimsonDk: '#7a1929',
  gold:      '#d4a24a',
  goldHi:    '#ecc777',
  goldDim:   '#8e6e2d',
  bronze:    '#cd7f32',

  // Type
  silver:  '#c9d2e2',
  ink:     '#f1f4fa',
  muted:   '#8696b3',
  muteDim: '#5a6a87',

  // System
  green: '#4ade80',
  red:   '#f87171',
};

export const radii = {
  sm: 4,
  md: 6,
  lg: 10,
};

export const fontFamily = {
  display: 'Oswald_600SemiBold',
  displayMedium: 'Oswald_500Medium',
  displayBold: 'Oswald_700Bold',
  body: 'Inter_400Regular',
  bodyMedium: 'Inter_500Medium',
  bodySemiBold: 'Inter_600SemiBold',
  mono: 'JetBrainsMono_400Regular',
  monoMedium: 'JetBrainsMono_500Medium',
};

// Rank accent: 1 gold, 2 silver, 3 bronze, rest dim
export const rankColor = (r) =>
  r === 1 ? colors.gold : r === 2 ? colors.silver : r === 3 ? colors.bronze : colors.muteDim;

// Article type → pill accent (from design)
export const articleTypeColor = (type) => ({
  power_ranking: '#a8243a',
  trade_analysis: '#2563eb',
  matchup_breakdown: '#7c3aed',
  matchup_analysis: '#7c3aed',
  injury: '#d97706',
}[type] ?? '#059669');

export const articleTypeLabel = (type) => ({
  power_ranking: 'Power Rankings',
  trade_analysis: 'Trade Analysis',
  matchup_breakdown: 'Matchup Breakdown',
  matchup_analysis: 'Matchup Analysis',
  injury: 'Injury Report',
  rumors: 'Rumor Mill',
  team_analysis: 'Team Analysis',
}[type] ?? 'League News');
