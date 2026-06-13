import { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, fontFamily } from '../theme';
import { PosChip } from './atoms';

const POS_ORDER = { QB: 0, RB: 1, WR: 2, TE: 3, K: 4, DEF: 5 };
const sortPlayers = (players) =>
  [...players].sort(
    (a, b) =>
      (POS_ORDER[a.position] ?? 9) - (POS_ORDER[b.position] ?? 9) ||
      (a.depth_chart_order ?? 99) - (b.depth_chart_order ?? 99)
  );

const TABS = [
  ['starters', 'Starters'],
  ['bench', 'Bench'],
  ['taxi', 'Taxi'],
];

const injuryColor = (status) =>
  status === 'Out' || status === 'IR' ? colors.red : '#d97706';

const RosterBlock = ({ players = [] }) => {
  const [tab, setTab] = useState('starters');
  const filtered = sortPlayers(
    players.filter((p) =>
      tab === 'starters' ? p.starter : tab === 'taxi' ? p.taxi : !p.starter && !p.taxi
    )
  );

  return (
    <View>
      <View style={styles.tabs}>
        {TABS.map(([id, label]) => (
          <TouchableOpacity
            key={id}
            onPress={() => setTab(id)}
            style={[styles.tab, tab === id && styles.tabActive]}
          >
            <Text style={[styles.tabText, tab === id && styles.tabTextActive]}>{label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      {filtered.map((p, i) => (
        <View
          key={p.player_id ?? i}
          style={[styles.row, { backgroundColor: i % 2 === 0 ? colors.field800 : colors.field900 }]}
        >
          <PosChip pos={p.position} />
          <View style={styles.info}>
            <Text style={styles.name}>{p.first_name} {p.last_name}</Text>
            <Text style={styles.meta}>
              {p.nfl_team ?? 'FA'}
              {p.age ? `  ·  ${p.age} yrs` : ''}
            </Text>
          </View>
          {p.injury_status ? (
            <Text style={[styles.injury, { color: injuryColor(p.injury_status) }]}>
              {p.injury_status.toUpperCase()}
            </Text>
          ) : p.taxi ? (
            <Text style={styles.taxiTag}>TAXI</Text>
          ) : null}
        </View>
      ))}
      {filtered.length === 0 && (
        <View style={styles.empty}>
          <Text style={styles.emptyText}>No players</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  tabs: {
    backgroundColor: colors.field700,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    flexDirection: 'row',
  },
  tab: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabActive: {
    borderBottomColor: colors.gold,
  },
  tabText: {
    fontFamily: fontFamily.display,
    fontSize: 11,
    letterSpacing: 1.1,
    textTransform: 'uppercase',
    color: colors.muteDim,
  },
  tabTextActive: {
    color: colors.gold,
  },
  row: {
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 10,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  info: {
    flex: 1,
    minWidth: 0,
  },
  name: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
  meta: {
    fontFamily: fontFamily.mono,
    fontSize: 10,
    color: colors.muteDim,
    marginTop: 1,
  },
  injury: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    letterSpacing: 0.5,
  },
  taxiTag: {
    fontFamily: fontFamily.mono,
    fontSize: 10,
    color: colors.muteDim,
  },
  empty: {
    padding: 24,
    alignItems: 'center',
  },
  emptyText: {
    fontFamily: fontFamily.mono,
    fontSize: 11,
    color: colors.muteDim,
  },
});

export default RosterBlock;
