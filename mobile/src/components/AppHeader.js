import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, fontFamily } from '../theme';
import { IcBack } from './icons';

const AppHeader = ({ title, pre, sub, back, onBack, right }) => (
  <View style={styles.bar}>
    <View style={styles.left}>
      {back && (
        <TouchableOpacity onPress={onBack} style={styles.backBtn} hitSlop={8}>
          <IcBack />
        </TouchableOpacity>
      )}
      <View style={{ flexShrink: 1 }}>
        {pre ? <Text style={styles.pre}>{pre}</Text> : null}
        <Text style={[styles.title, back ? styles.titleBack : styles.titleMain]} numberOfLines={1}>
          {title}
        </Text>
        {sub ? <Text style={styles.sub}>{sub}</Text> : null}
      </View>
    </View>
    {right ? <View>{right}</View> : null}
  </View>
);

const styles = StyleSheet.create({
  bar: {
    backgroundColor: colors.field900,
    borderBottomWidth: 1,
    borderBottomColor: colors.hairline,
    paddingVertical: 10,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  left: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 9,
    flexShrink: 1,
  },
  backBtn: {
    paddingVertical: 4,
    paddingRight: 8,
  },
  pre: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
    letterSpacing: 1.3,
    textTransform: 'uppercase',
    marginBottom: 1,
  },
  title: {
    fontFamily: fontFamily.display,
    textTransform: 'uppercase',
    lineHeight: 24,
  },
  titleMain: {
    fontSize: 20,
    color: colors.gold,
    letterSpacing: 1,
  },
  titleBack: {
    fontSize: 16,
    color: colors.ink,
    letterSpacing: 0.5,
  },
  sub: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
    letterSpacing: 1.1,
    textTransform: 'uppercase',
    marginTop: 2,
  },
});

export default AppHeader;
