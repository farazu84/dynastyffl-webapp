import { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  StatusBar,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, radii, fontFamily } from '../theme';
import config from '../config';

const RANK_COLORS = [colors.gold, colors.silver, colors.bronze];

const TeamRow = ({ team, rank }) => {
  const record = team.current_team_record;
  const rankColor = rank <= 3 ? RANK_COLORS[rank - 1] : colors.muted;
  const ownerName =
    team?.owners?.map(o => o.user_name).filter(Boolean).join(', ') ||
    team?.team_owners?.map(o => o.user?.user_name).filter(Boolean).join(', ') ||
    null;

  return (
    <View style={styles.teamRow}>
      <Text style={[styles.teamRank, { color: rankColor }]}>
        {String(rank).padStart(2, '0')}
      </Text>
      <View style={styles.teamLeft}>
        <Text style={styles.teamName}>{team.team_name}</Text>
        {ownerName && <Text style={styles.teamOwner}>{ownerName}</Text>}
      </View>
      {record && (
        <View style={styles.teamStats}>
          <Text style={styles.teamRecord}>
            <Text style={styles.wins}>{record.wins}</Text>
            <Text style={styles.separator}> · </Text>
            <Text style={styles.losses}>{record.losses}</Text>
          </Text>
          <Text style={styles.teamPoints}>
            <Text style={styles.statLabel}>PF </Text>
            <Text style={styles.statValue}>{record.points_for?.toFixed(1) ?? '0.0'}</Text>
            <Text style={styles.separator}>  ·  </Text>
            <Text style={styles.statLabel}>PA </Text>
            <Text style={styles.statValue}>{record.points_against?.toFixed(1) ?? '0.0'}</Text>
          </Text>
        </View>
      )}
    </View>
  );
};

export default function HomeScreen() {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTeams = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`${config.API_BASE_URL}/teams`);
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      const data = await res.json();
      setTeams(data.teams ?? []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchTeams(); }, []);

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor={colors.field900} />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerBrand}>
          <Text style={styles.headerPre}>Est. 2018 · San Jose</Text>
          <Text style={styles.headerTitle}>408 Gridiron</Text>
          <Text style={styles.headerSub}>Fantasy Football League</Text>
        </View>
      </View>

      {/* Standings */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Team Standings</Text>
      </View>

      {loading && (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.gold} />
          <Text style={styles.loadingText}>Loading league data…</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>Error: {error}</Text>
          <TouchableOpacity onPress={fetchTeams} style={styles.retryBtn}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      )}

      {!loading && !error && (
        <FlatList
          data={teams}
          keyExtractor={item => String(item.team_id)}
          renderItem={({ item, index }) => (
            <TeamRow team={item} rank={index + 1} />
          )}
          ItemSeparatorComponent={() => <View style={styles.divider} />}
          contentContainerStyle={styles.listContent}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.field800,
  },

  // Header
  header: {
    backgroundColor: colors.field900,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
    paddingVertical: 14,
    paddingHorizontal: 16,
    alignItems: 'center',
  },
  headerBrand: {
    alignItems: 'center',
  },
  headerPre: {
    fontFamily: fontFamily.mono,
    fontSize: 10,
    color: colors.muted,
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    marginBottom: 2,
  },
  headerTitle: {
    fontFamily: fontFamily.display,
    fontSize: 26,
    color: colors.gold,
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  headerSub: {
    fontFamily: fontFamily.mono,
    fontSize: 10,
    color: colors.muteDim,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    marginTop: 2,
  },

  // Section
  sectionHeader: {
    backgroundColor: colors.field700,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontFamily: fontFamily.display,
    fontSize: 14,
    color: colors.silver,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
  },

  // Team rows
  listContent: {
    paddingBottom: 24,
  },
  teamRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.field800,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  teamRank: {
    fontFamily: fontFamily.display,
    fontSize: 18,
    width: 32,
    marginRight: 12,
  },
  teamLeft: {
    flex: 1,
  },
  teamName: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 15,
    color: colors.ink,
  },
  teamOwner: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.muted,
    marginTop: 2,
  },
  teamStats: {
    alignItems: 'flex-end',
  },
  teamRecord: {
    fontFamily: fontFamily.display,
    fontSize: 15,
    color: colors.silver,
  },
  wins: {
    color: colors.green,
  },
  losses: {
    color: colors.red,
  },
  separator: {
    color: colors.muteDim,
  },
  teamPoints: {
    fontFamily: fontFamily.mono,
    fontSize: 11,
    color: colors.muted,
    marginTop: 2,
  },
  statLabel: {
    color: colors.muteDim,
  },
  statValue: {
    color: colors.silver,
  },
  divider: {
    height: 1,
    backgroundColor: colors.stroke,
    marginLeft: 60,
  },

  // States
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
  },
  loadingText: {
    fontFamily: fontFamily.mono,
    fontSize: 12,
    color: colors.muted,
    letterSpacing: 0.8,
  },
  errorBox: {
    margin: 16,
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.crimson,
    borderRadius: radii.md,
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
    borderRadius: radii.sm,
    paddingVertical: 8,
    paddingHorizontal: 20,
  },
  retryText: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
});
