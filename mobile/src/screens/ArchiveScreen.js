import { useState, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  ScrollView,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, fontFamily } from '../theme';
import { apiGet } from '../api';
import AppHeader from '../components/AppHeader';
import SectionHeader from '../components/SectionHeader';
import { IcTrophy } from '../components/icons';

const fmtDate = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: '2-digit' });
};

// Derive the two team names and the assets each side received
const summarizeTrade = (t) => {
  const teams = (t.roster_moves ?? []).map((r) => r.team?.team_name).filter(Boolean);
  const assets = [];
  const seen = new Set();
  for (const pm of t.player_moves ?? []) {
    if (pm.action !== 'add' || !pm.player) continue;
    const name = `${pm.player.first_name} ${pm.player.last_name}`;
    if (seen.has(name)) continue;
    seen.add(name);
    assets.push({ label: name, pick: false });
  }
  for (const dp of t.draft_pick_moves ?? []) {
    assets.push({ label: `${dp.season} R${dp.round}`, pick: true });
  }
  return { teams, assets };
};

const TradeCard = ({ trade, index }) => {
  const { teams, assets } = summarizeTrade(trade);
  return (
    <View style={[styles.tradeCard, { backgroundColor: index % 2 === 0 ? colors.field800 : colors.field900 }]}>
      <View style={styles.tradeHeader}>
        <Text style={styles.tradeTeams} numberOfLines={2}>
          <Text style={{ color: colors.gold }}>{teams[0] ?? '—'}</Text>
          <Text style={{ color: colors.muteDim }}>  ↔  </Text>
          <Text style={{ color: colors.gold }}>{teams[1] ?? '—'}</Text>
        </Text>
        <Text style={styles.tradeMeta}>
          Wk {trade.week} · {fmtDate(trade.created_at)}
        </Text>
      </View>
      <View style={styles.assetWrap}>
        {assets.map((a, i) => (
          <View key={i} style={styles.assetChip}>
            <Text style={[styles.assetText, a.pick && { fontFamily: fontFamily.mono, color: '#7fb3e8' }]}>
              {a.label}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
};

const RECORD_DEFS = [
  // [superlative source, category key, row label, value fn, stat fn]
  ['teams', 'most_trades', 'Most Trade Volume', (x) => x.team_name, (x) => `${x.trade_count} trades`],
  ['teams', 'waiver_warriors', 'Waiver Warrior', (x) => x.team_name, (x) => `${x.pickup_count} pickups`],
  ['teams', 'draft_capital_movers', 'Draft Capital Mover', (x) => x.team_name, (x) => `${x.picks_traded} picks`],
  ['teams', 'frequent_trade_partners', 'Frequent Trade Partners', (x) => `${x.team_1} & ${x.team_2}`, (x) => `${x.trade_count} trades`],
  ['players', 'most_traded', 'Most Traded Player', (x) => `${x.first_name} ${x.last_name} (${x.position})`, (x) => `${x.trade_count} trades`],
  ['players', 'most_dropped', 'Most Dropped Player', (x) => `${x.first_name} ${x.last_name} (${x.position})`, (x) => `${x.drop_count} drops`],
  ['players', 'most_teams', 'League Journeyman', (x) => `${x.first_name} ${x.last_name} (${x.position})`, (x) => `${x.team_count} teams`],
  ['players', 'boomerang', 'The Boomerang', (x) => `${x.first_name} ${x.last_name} (${x.position})`, (x) => `${x.times_added}× returned`],
];

export default function ArchiveScreen() {
  const [view, setView] = useState('trades');
  const [trades, setTrades] = useState(null);
  const [records, setRecords] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    Promise.all([
      apiGet('/transactions?type=trade'),
      apiGet('/superlatives/teams').catch(() => null),
      apiGet('/superlatives/players').catch(() => null),
    ])
      .then(([tradesRes, teamSup, playerSup]) => {
        setTrades(tradesRes.transactions ?? []);
        const sup = { teams: teamSup?.superlatives ?? {}, players: playerSup?.superlatives ?? {} };
        setRecords(
          RECORD_DEFS.flatMap(([src, key, label, valueFn, statFn]) => {
            const first = sup[src][key]?.[0];
            return first ? [{ label, value: valueFn(first), stat: statFn(first) }] : [];
          })
        );
      })
      .catch((e) => setError(e.message));
  }, []);

  const loading = trades === null && !error;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <AppHeader title="Archive" sub="Est. 2018" />
      <View style={styles.segTabs}>
        {[['trades', 'Trade History'], ['records', 'Records']].map(([id, label]) => (
          <TouchableOpacity
            key={id}
            onPress={() => setView(id)}
            style={[styles.segTab, view === id && styles.segTabActive]}
          >
            <Text style={[styles.segTabText, view === id && { color: colors.gold }]}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {loading && (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      )}
      {error && (
        <View style={styles.centered}>
          <Text style={styles.errorText}>Error loading archive: {error}</Text>
        </View>
      )}

      {!loading && !error && view === 'trades' && (
        <FlatList
          data={trades}
          keyExtractor={(t) => String(t.transaction_id)}
          ListHeaderComponent={
            <SectionHeader label="All Trades" right={`${trades.length} all-time`} />
          }
          renderItem={({ item, index }) => <TradeCard trade={item} index={index} />}
          ListFooterComponent={<View style={{ height: 16 }} />}
        />
      )}

      {!loading && !error && view === 'records' && (
        <ScrollView>
          <SectionHeader label="League Records" right="All-time" />
          {(records ?? []).map((r, i) => (
            <View
              key={r.label}
              style={[styles.recordRow, { backgroundColor: i % 2 === 0 ? colors.field800 : colors.field900 }]}
            >
              <View style={styles.recordIcon}>
                <IcTrophy c={i < 2 ? colors.gold : colors.muteDim} s={15} />
              </View>
              <View style={styles.recordInfo}>
                <Text style={styles.recordLabel}>{r.label}</Text>
                <Text style={styles.recordValue} numberOfLines={1}>{r.value}</Text>
              </View>
              <Text style={styles.recordStat}>{r.stat}</Text>
            </View>
          ))}
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
  segTabs: {
    backgroundColor: colors.field700,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    flexDirection: 'row',
  },
  segTab: {
    flex: 1,
    paddingVertical: 11,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  segTabActive: {
    borderBottomColor: colors.gold,
  },
  segTabText: {
    fontFamily: fontFamily.display,
    fontSize: 11,
    letterSpacing: 1.2,
    textTransform: 'uppercase',
    color: colors.muteDim,
  },

  // Trades
  tradeCard: {
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  tradeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  tradeTeams: {
    flex: 1,
    fontFamily: fontFamily.display,
    fontSize: 13,
    lineHeight: 17,
  },
  tradeMeta: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
  },
  assetWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 5,
  },
  assetChip: {
    backgroundColor: colors.field600,
    borderWidth: 1,
    borderColor: colors.stroke2,
    borderRadius: 4,
    paddingVertical: 3,
    paddingHorizontal: 8,
  },
  assetText: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    color: colors.silver,
  },

  // Records
  recordRow: {
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  recordIcon: {
    width: 30,
    height: 30,
    borderRadius: 6,
    backgroundColor: colors.field600,
    borderWidth: 1,
    borderColor: colors.stroke2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  recordInfo: {
    flex: 1,
    minWidth: 0,
  },
  recordLabel: {
    fontFamily: fontFamily.mono,
    fontSize: 9.5,
    color: colors.muteDim,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 2,
  },
  recordValue: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
  recordStat: {
    fontFamily: fontFamily.displayBold,
    fontSize: 14,
    color: colors.gold,
    letterSpacing: 0.3,
  },
});
