import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, fontFamily, rankColor } from '../theme';
import { apiGet } from '../api';
import AppHeader from '../components/AppHeader';
import SectionHeader from '../components/SectionHeader';
import { IcChev, IcLive } from '../components/icons';
import { isGameDay } from '../components/MatchupCard';

const fmtScore = (s) => (s !== undefined && s !== null ? s.toFixed(1) : '—');

// One record per team comes back; dedupe to one card per game
const dedupeMatchups = (matchups) => {
  const seen = new Set();
  return matchups.filter((m) => {
    const key = m.sleeper_matchup_id ?? m.matchup_id;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
};

const sortTeams = (teams) =>
  [...teams].sort((a, b) => {
    const ra = a.current_team_record, rb = b.current_team_record;
    return (rb?.wins ?? 0) - (ra?.wins ?? 0) || (rb?.points_for ?? 0) - (ra?.points_for ?? 0);
  });

const MatchupStripCard = ({ m, live }) => (
  <View style={styles.stripCard}>
    {[
      { name: m.team?.team_name, score: m.points_for },
      { name: m.opponent_team?.team_name, score: m.points_against },
    ].map((side, i) => {
      const otherScore = i === 0 ? m.points_against : m.points_for;
      const winning = side.score != null && otherScore != null && side.score > otherScore;
      return (
        <View key={i} style={[styles.stripRow, i === 0 && { marginBottom: 5 }]}>
          <Text style={[styles.stripName, winning && styles.stripNameWin]} numberOfLines={1}>
            {side.name ?? 'TBD'}
          </Text>
          <Text style={[styles.stripScore, { color: winning ? colors.gold : colors.muted }]}>
            {fmtScore(side.score)}
          </Text>
        </View>
      );
    })}
    <View style={styles.stripStatus}>
      {m.completed ? (
        <Text style={styles.stripStatusText}>FINAL</Text>
      ) : live ? (
        <>
          <IcLive s={6} />
          <Text style={[styles.stripStatusText, { color: colors.red }]}>LIVE</Text>
        </>
      ) : (
        <Text style={styles.stripStatusText}>PREVIEW</Text>
      )}
    </View>
  </View>
);

export default function HomeScreen({ navigation }) {
  const [teams, setTeams] = useState([]);
  const [matchups, setMatchups] = useState([]);
  const [leagueState, setLeagueState] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);
      const [teamsRes, matchupsRes, stateRes] = await Promise.all([
        apiGet('/teams'),
        apiGet('/matchups/current_matchups').catch(() => null),
        apiGet('/league/state').catch(() => null),
      ]);
      setTeams(sortTeams(teamsRes.teams ?? []));
      setMatchups(dedupeMatchups(matchupsRes?.matchups ?? []));
      setLeagueState(stateRes?.success ? stateRes : null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const week = leagueState?.current_week || null;
  const year = leagueState?.current_year || null;
  const live = isGameDay(week ?? 0);

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <AppHeader title="408 Gridiron" pre="Est. 2018 · San Jose" sub="Fantasy Football League" />
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.gold} />
          <Text style={styles.loadingText}>Loading league data…</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <AppHeader
        title="408 Gridiron"
        pre="Est. 2018 · San Jose"
        sub="Fantasy Football League"
        right={
          week ? (
            <View style={styles.weekBadge}>
              <Text style={styles.weekBadgeText}>Week {week}</Text>
            </View>
          ) : null
        }
      />
      <ScrollView
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); fetchData(); }}
            tintColor={colors.gold}
          />
        }
      >
        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>Error loading data: {error}</Text>
            <TouchableOpacity onPress={fetchData} style={styles.retryBtn}>
              <Text style={styles.retryText}>Retry</Text>
            </TouchableOpacity>
          </View>
        )}

        {matchups.length > 0 && (
          <>
            <SectionHeader
              label="Current Matchups"
              right={
                live ? (
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                    <IcLive />
                    <Text style={{ fontFamily: fontFamily.mono, fontSize: 9, color: colors.red }}>LIVE</Text>
                  </View>
                ) : (
                  `Week ${week ?? '—'}`
                )
              }
            />
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              style={styles.strip}
              contentContainerStyle={styles.stripContent}
            >
              {matchups.map((m) => (
                <MatchupStripCard key={m.matchup_id} m={m} live={live && !m.completed} />
              ))}
            </ScrollView>
          </>
        )}

        <SectionHeader label="Team Standings" right={year ? `${year} Season` : undefined} />
        {teams.map((team, index) => {
          const rank = index + 1;
          const record = team.current_team_record;
          const ownerName = team.owners?.map((o) => o.user_name).filter(Boolean).join(', ');
          return (
            <TouchableOpacity
              key={team.team_id}
              onPress={() => navigation.navigate('TeamDetail', { teamId: team.team_id, teamName: team.team_name })}
              style={[styles.teamRow, { backgroundColor: rank % 2 === 0 ? colors.field800 : colors.field900 }]}
            >
              <Text style={[styles.teamRank, { color: rankColor(rank) }]}>
                {String(rank).padStart(2, '0')}
              </Text>
              <View style={styles.teamInfo}>
                <Text style={styles.teamName} numberOfLines={1}>{team.team_name}</Text>
                <Text style={styles.teamOwner} numberOfLines={1}>
                  {ownerName}
                  {team.championships > 0 && (
                    <Text style={{ color: colors.goldDim }}>  {team.championships}× champ</Text>
                  )}
                </Text>
              </View>
              <View style={styles.teamStats}>
                <Text style={styles.teamRecord}>
                  <Text style={{ color: colors.green }}>{record?.wins ?? 0}</Text>
                  <Text style={{ color: colors.muteDim }}> · </Text>
                  <Text style={{ color: colors.red }}>{record?.losses ?? 0}</Text>
                </Text>
                <Text style={styles.teamPf}>{(record?.points_for ?? 0).toFixed(1)}</Text>
              </View>
              <IcChev />
            </TouchableOpacity>
          );
        })}
        <View style={{ height: 16 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.field800,
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontFamily: fontFamily.mono,
    fontSize: 11,
    color: colors.muted,
    letterSpacing: 0.8,
  },
  weekBadge: {
    backgroundColor: colors.crimsonDk + '33',
    borderWidth: 1,
    borderColor: colors.crimson + '55',
    borderRadius: 4,
    paddingVertical: 3,
    paddingHorizontal: 8,
  },
  weekBadgeText: {
    fontFamily: fontFamily.displayBold,
    fontSize: 12,
    color: colors.crimson,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },

  // Matchup strip
  strip: {
    backgroundColor: colors.field800,
    flexGrow: 0,
  },
  stripContent: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    gap: 10,
  },
  stripCard: {
    minWidth: 136,
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  stripRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 8,
  },
  stripName: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    color: colors.muted,
    flex: 1,
  },
  stripNameWin: {
    fontFamily: fontFamily.bodySemiBold,
    color: colors.ink,
  },
  stripScore: {
    fontFamily: fontFamily.displayBold,
    fontSize: 15,
    letterSpacing: 0.3,
  },
  stripStatus: {
    borderTopWidth: 1,
    borderTopColor: colors.stroke,
    marginTop: 7,
    paddingTop: 5,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  stripStatusText: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
    letterSpacing: 1,
  },

  // Standings
  teamRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 11,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
  },
  teamRank: {
    fontFamily: fontFamily.display,
    fontSize: 16,
    width: 26,
    textAlign: 'right',
  },
  teamInfo: {
    flex: 1,
    minWidth: 0,
  },
  teamName: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
  teamOwner: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    color: colors.muted,
    marginTop: 1,
  },
  teamStats: {
    alignItems: 'flex-end',
  },
  teamRecord: {
    fontFamily: fontFamily.display,
    fontSize: 14,
    letterSpacing: 0.3,
  },
  teamPf: {
    fontFamily: fontFamily.mono,
    fontSize: 9.5,
    color: colors.muteDim,
    marginTop: 1,
  },

  // Error
  errorBox: {
    margin: 16,
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.crimson,
    borderRadius: 6,
    padding: 16,
    alignItems: 'center',
    gap: 12,
  },
  errorText: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    color: colors.red,
    textAlign: 'center',
  },
  retryBtn: {
    backgroundColor: colors.field600,
    borderWidth: 1,
    borderColor: colors.stroke2,
    borderRadius: 4,
    paddingVertical: 8,
    paddingHorizontal: 20,
  },
  retryText: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
});
