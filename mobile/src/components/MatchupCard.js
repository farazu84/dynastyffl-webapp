import { View, Text, StyleSheet } from 'react-native';
import { colors, fontFamily } from '../theme';
import { IcLive } from './icons';

// Thu=4, Fri=5, Sat=6, Sun=0, Mon=1 — mirrors web ScoreboardStrip
const GAME_DAYS = new Set([4, 5, 6, 0, 1]);
export const isGameDay = (week) =>
  GAME_DAYS.has(new Date().getDay()) && week >= 1 && week <= 20;

const fmtScore = (s) => (s !== undefined && s !== null ? s.toFixed(1) : '—');

const MatchupCard = ({ matchup, week }) => {
  if (!matchup) return null;
  const live = !matchup.completed && isGameDay(week);
  const me = matchup.points_for;
  const them = matchup.points_against;
  const winning = me != null && them != null && me >= them;

  return (
    <View style={styles.card}>
      <Text style={styles.eyebrow}>{week ? `Week ${week} Matchup` : 'Matchup'}</Text>
      <View style={styles.row}>
        <View style={styles.side}>
          <Text style={styles.name} numberOfLines={1}>{matchup.team?.team_name ?? 'TBD'}</Text>
          <Text style={[styles.score, { color: winning ? colors.gold : colors.silver }]}>{fmtScore(me)}</Text>
        </View>
        <View style={styles.mid}>
          <Text style={styles.vs}>VS</Text>
          <View style={styles.status}>
            {matchup.completed ? (
              <Text style={styles.statusText}>FINAL</Text>
            ) : live ? (
              <>
                <IcLive s={6} />
                <Text style={[styles.statusText, { color: colors.red }]}>LIVE</Text>
              </>
            ) : (
              <Text style={styles.statusText}>PREVIEW</Text>
            )}
          </View>
        </View>
        <View style={[styles.side, { alignItems: 'flex-end' }]}>
          <Text style={[styles.name, { color: colors.muted }]} numberOfLines={1}>
            {matchup.opponent_team?.team_name ?? 'TBD'}
          </Text>
          <Text style={[styles.score, { color: colors.muted }]}>{fmtScore(them)}</Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.field800,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  eyebrow: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  side: {
    flex: 1,
    minWidth: 0,
  },
  name: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
  score: {
    fontFamily: fontFamily.displayBold,
    fontSize: 22,
    letterSpacing: 0.5,
    marginTop: 2,
  },
  mid: {
    alignItems: 'center',
    paddingHorizontal: 16,
  },
  vs: {
    fontFamily: fontFamily.display,
    fontSize: 11,
    color: colors.muteDim,
    letterSpacing: 1.3,
  },
  status: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  statusText: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
  },
});

export default MatchupCard;
