import { View, Text, StyleSheet } from 'react-native';
import { colors, fontFamily } from '../theme';

const SectionHeader = ({ label, right }) => (
  <View style={styles.bar}>
    <Text style={styles.label}>{label}</Text>
    {right ? (
      typeof right === 'string' ? <Text style={styles.right}>{right}</Text> : right
    ) : null}
  </View>
);

const styles = StyleSheet.create({
  bar: {
    backgroundColor: colors.field700,
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  label: {
    fontFamily: fontFamily.display,
    fontSize: 11,
    color: colors.silver,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },
  right: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
    letterSpacing: 0.5,
  },
});

export default SectionHeader;
