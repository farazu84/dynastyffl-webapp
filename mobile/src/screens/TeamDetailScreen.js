import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, fontFamily } from '../theme';
import { apiGet } from '../api';
import AppHeader from '../components/AppHeader';
import SectionHeader from '../components/SectionHeader';
import MatchupCard from '../components/MatchupCard';
import RosterBlock from '../components/RosterBlock';
import ArticleRow from '../components/ArticleRow';
import { IcTrophy } from '../components/icons';

export default function TeamDetailScreen({ route, navigation }) {
  const { teamId, teamName } = route.params;
  const [team, setTeam] = useState(null);
  const [matchup, setMatchup] = useState(null);
  const [week, setWeek] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const [teamRes, matchupsRes, stateRes] = await Promise.all([
          apiGet(`/teams/${teamId}`),
          apiGet('/matchups/current_matchups').catch(() => null),
          apiGet('/league/state').catch(() => null),
        ]);
        setTeam(teamRes.team);
        setMatchup(
          (matchupsRes?.matchups ?? []).find((m) => m.team?.team_id === teamId) ?? null
        );
        if (stateRes?.success) setWeek(stateRes.current_week);
      } catch (e) {
        setError(e.message);
      }
    })();
  }, [teamId]);

  const record = team?.current_team_record;
  const gp = (record?.wins ?? 0) + (record?.losses ?? 0);
  const avgWk = gp > 0 ? ((record?.points_for ?? 0) / gp).toFixed(1) : '—';
  const ownerName = team?.owners?.map((o) => o.user_name).filter(Boolean).join(', ');

  const stats = [
    { label: 'Record', value: record ? `${record.wins}–${record.losses}` : '—', hi: true },
    { label: 'Pts For', value: record ? record.points_for.toFixed(1) : '—' },
    { label: 'Avg/Wk', value: avgWk },
    { label: 'Avg Age', value: team?.average_age != null ? team.average_age.toFixed(1) : '—' },
  ];

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <AppHeader title={team?.team_name ?? teamName} back onBack={() => navigation.goBack()} />
      {!team && !error && (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      )}
      {error && (
        <View style={styles.centered}>
          <Text style={styles.errorText}>Error loading team: {error}</Text>
        </View>
      )}
      {team && (
        <ScrollView>
          <View style={styles.hero}>
            <View style={styles.ownerRow}>
              <Text style={styles.ownerText}>
                Owner <Text style={styles.ownerName}>{ownerName || '—'}</Text>
              </Text>
              {team.championships > 0 && (
                <View style={styles.champBadge}>
                  <IcTrophy s={12} />
                  <Text style={styles.champText}>{team.championships}× Champ</Text>
                </View>
              )}
            </View>
            <View style={styles.statStrip}>
              {stats.map((s, i) => (
                <View key={s.label} style={[styles.statCell, i < 3 && styles.statCellBorder]}>
                  <Text style={styles.statLabel}>{s.label}</Text>
                  <Text style={[styles.statValue, s.hi && { color: colors.gold }]}>{s.value}</Text>
                </View>
              ))}
            </View>
          </View>
          {matchup && <MatchupCard matchup={matchup} week={week} />}
          <SectionHeader
            label="Roster"
            right={team.roster_size ? `${team.roster_size} players` : undefined}
          />
          <RosterBlock players={team.players ?? []} />
          {team.articles?.length > 0 && (
            <>
              <SectionHeader label="Related Coverage" right={`${team.articles.length} articles`} />
              {team.articles.map((a, i) => (
                <ArticleRow
                  key={a.article_id}
                  article={a}
                  index={i}
                  onPress={() => navigation.navigate('Article', { article: a })}
                />
              ))}
            </>
          )}
          <View style={{ height: 16 }} />
        </ScrollView>
      )}
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
    padding: 24,
  },
  errorText: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    color: colors.red,
    textAlign: 'center',
  },
  hero: {
    backgroundColor: colors.field900,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  ownerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 10,
  },
  ownerText: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.muted,
  },
  ownerName: {
    fontFamily: fontFamily.bodySemiBold,
    color: colors.silver,
  },
  champBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: colors.gold + '33',
    borderWidth: 1,
    borderColor: colors.gold + '66',
    borderRadius: 4,
    paddingVertical: 2,
    paddingHorizontal: 8,
  },
  champText: {
    fontFamily: fontFamily.displayBold,
    fontSize: 9,
    color: colors.gold,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  statStrip: {
    flexDirection: 'row',
  },
  statCell: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 4,
  },
  statCellBorder: {
    borderRightWidth: 1,
    borderRightColor: colors.stroke,
  },
  statLabel: {
    fontFamily: fontFamily.mono,
    fontSize: 8.5,
    color: colors.muteDim,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 3,
  },
  statValue: {
    fontFamily: fontFamily.displayBold,
    fontSize: 15,
    color: colors.silver,
    letterSpacing: 0.3,
  },
});
