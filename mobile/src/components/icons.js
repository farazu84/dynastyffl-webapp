import Svg, { Path, Rect, Circle } from 'react-native-svg';
import { colors } from '../theme';

export const IcHome = ({ c = colors.muteDim, s = 22 }) => (
  <Svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <Path d="M3 10.5L12 3l9 7.5V20a1 1 0 01-1 1H5a1 1 0 01-1-1v-9.5z" stroke={c} strokeWidth={1.75} strokeLinejoin="round" />
    <Path d="M9 21V13h6v8" stroke={c} strokeWidth={1.75} strokeLinejoin="round" />
  </Svg>
);

export const IcNews = ({ c = colors.muteDim, s = 22 }) => (
  <Svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <Rect x={3} y={4} width={18} height={16} rx={2} stroke={c} strokeWidth={1.75} />
    <Path d="M7 8h10M7 12h10M7 16h5" stroke={c} strokeWidth={1.75} strokeLinecap="round" />
  </Svg>
);

export const IcRumor = ({ c = colors.muteDim, s = 22 }) => (
  <Svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <Path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2v10z" stroke={c} strokeWidth={1.75} strokeLinejoin="round" />
    <Circle cx={9} cy={10} r={1} fill={c} />
    <Circle cx={12} cy={10} r={1} fill={c} />
    <Circle cx={15} cy={10} r={1} fill={c} />
  </Svg>
);

export const IcArchive = ({ c = colors.muteDim, s = 22 }) => (
  <Svg width={s} height={s} viewBox="0 0 24 24" fill="none">
    <Rect x={3} y={3} width={18} height={5} rx={1} stroke={c} strokeWidth={1.75} />
    <Path d="M5 8v12a1 1 0 001 1h12a1 1 0 001-1V8" stroke={c} strokeWidth={1.75} />
    <Path d="M10 13h4" stroke={c} strokeWidth={1.75} strokeLinecap="round" />
  </Svg>
);

export const IcChev = ({ c = colors.muteDim, s = 14 }) => (
  <Svg width={s} height={s} viewBox="0 0 14 14" fill="none">
    <Path d="M5 3l4 4-4 4" stroke={c} strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>
);

export const IcBack = ({ c = colors.gold, s = 20 }) => (
  <Svg width={s} height={s} viewBox="0 0 20 20" fill="none">
    <Path d="M13 4l-6 6 6 6" stroke={c} strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>
);

export const IcLive = ({ c = colors.red, s = 7 }) => (
  <Svg width={s} height={s} viewBox="0 0 7 7">
    <Circle cx={3.5} cy={3.5} r={3.5} fill={c} />
  </Svg>
);

export const IcTrophy = ({ c = colors.gold, s = 16 }) => (
  <Svg width={s} height={s} viewBox="0 0 16 16" fill="none">
    <Path d="M5 2h6v6a3 3 0 01-6 0V2z" stroke={c} strokeWidth={1.4} strokeLinejoin="round" />
    <Path d="M5 5H3a2 2 0 000 4h2M11 5h2a2 2 0 010 4h-2" stroke={c} strokeWidth={1.4} strokeLinecap="round" />
    <Path d="M8 11v2M5.5 13h5" stroke={c} strokeWidth={1.4} strokeLinecap="round" />
  </Svg>
);

export const IcInfo = ({ c = colors.muted, s = 18 }) => (
  <Svg width={s} height={s} viewBox="0 0 18 18" fill="none">
    <Circle cx={9} cy={9} r={8} stroke={c} strokeWidth={1.4} />
    <Path d="M9 8v5M9 6h.01" stroke={c} strokeWidth={1.6} strokeLinecap="round" />
  </Svg>
);

export const IcCheck = ({ c = colors.green, s = 26 }) => (
  <Svg width={s} height={s} viewBox="0 0 26 26" fill="none">
    <Path d="M4 13l6 6L22 7" stroke={c} strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>
);

export const IcCaret = ({ c = colors.muteDim, s = 12, open = false }) => (
  <Svg width={s} height={s * 0.66} viewBox="0 0 12 8" fill="none" style={{ transform: [{ rotate: open ? '180deg' : '0deg' }] }}>
    <Path d="M1 1.5l5 5 5-5" stroke={c} strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>
);

export const IcSwap = ({ c = colors.gold, s = 16 }) => (
  <Svg width={s} height={s} viewBox="0 0 16 16" fill="none">
    <Path d="M3 6h9l-2.2-2.2M13 10H4l2.2 2.2" stroke={c} strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" />
  </Svg>
);
