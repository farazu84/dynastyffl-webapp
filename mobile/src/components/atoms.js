import { View, Text, StyleSheet } from 'react-native';
import { colors, fontFamily } from '../theme';

export const PosChip = ({ pos }) => (
  <View style={styles.posChip}>
    <Text style={styles.posChipText}>{pos}</Text>
  </View>
);

export const TypePill = ({ label, acct }) => (
  <View style={[styles.typePill, { backgroundColor: acct + '1a', borderColor: acct + '40' }]}>
    <Text style={[styles.typePillText, { color: acct }]}>{label}</Text>
  </View>
);

const styles = StyleSheet.create({
  posChip: {
    backgroundColor: colors.field600,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 3,
    paddingVertical: 2,
    paddingHorizontal: 5,
    minWidth: 38,
    alignItems: 'center',
  },
  posChipText: {
    fontFamily: fontFamily.display,
    fontSize: 10,
    color: colors.muteDim,
    letterSpacing: 0.6,
  },
  typePill: {
    borderWidth: 1,
    borderRadius: 3,
    paddingVertical: 2,
    paddingHorizontal: 7,
    alignSelf: 'flex-start',
  },
  typePillText: {
    fontFamily: fontFamily.display,
    fontSize: 9,
    letterSpacing: 0.9,
    textTransform: 'uppercase',
  },
});
