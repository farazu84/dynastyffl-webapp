import { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, fontFamily } from '../theme';
import { apiGet, apiPost } from '../api';
import AppHeader from '../components/AppHeader';
import { IcInfo, IcCheck, IcCaret } from '../components/icons';

const MAX_LEN = 500;

export default function RumorsScreen() {
  const [text, setText] = useState('');
  const [teams, setTeams] = useState([]);
  const [selected, setSelected] = useState([]);
  const [open, setOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiGet('/teams')
      .then((res) => setTeams(res.teams ?? []))
      .catch(() => {});
  }, []);

  const toggle = (id) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const submit = async () => {
    if (!text.trim() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      await apiPost('/articles/generate_rumor', { rumor: text.trim(), team_ids: selected });
      setDone(true);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  const reset = () => {
    setDone(false);
    setText('');
    setSelected([]);
    setOpen(false);
    setError(null);
  };

  if (done) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['top']}>
        <AppHeader title="Rumor Mill" />
        <View style={styles.doneWrap}>
          <View style={styles.doneCircle}>
            <IcCheck />
          </View>
          <Text style={styles.doneTitle}>Rumor Submitted</Text>
          <Text style={styles.doneBody}>
            Your anonymous tip has been received. An AI-generated article may follow.
          </Text>
          <TouchableOpacity onPress={reset} style={styles.againBtn}>
            <Text style={styles.againText}>Submit Another</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const canSubmit = !!text.trim() && !submitting;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <AppHeader title="Rumor Mill" />
      <KeyboardAvoidingView
        style={{ flex: 1 }}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <View style={styles.infoBanner}>
            <IcInfo />
            <Text style={styles.infoText}>
              All rumors are completely <Text style={styles.infoStrong}>anonymous</Text>. Be
              specific about players and teams involved.
            </Text>
          </View>

          <View>
            <Text style={styles.fieldLabel}>The Rumor</Text>
            <TextInput
              value={text}
              onChangeText={(v) => setText(v.slice(0, MAX_LEN))}
              placeholder="I heard that…"
              placeholderTextColor={colors.muteDim}
              multiline
              maxLength={MAX_LEN}
              style={[styles.textarea, text ? { borderColor: colors.stroke2 } : null]}
            />
            <Text style={styles.counter}>{text.length}/{MAX_LEN}</Text>
          </View>

          <View>
            <TouchableOpacity
              onPress={() => setOpen((o) => !o)}
              style={[styles.tagToggle, open && styles.tagToggleOpen]}
            >
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.fieldLabel}>Tag Teams</Text>
                {selected.length > 0 && (
                  <Text style={styles.tagCount}>{selected.length} tagged</Text>
                )}
              </View>
              <IcCaret open={open} />
            </TouchableOpacity>
            {open && (
              <View style={styles.teamList}>
                {teams.map((t) => {
                  const on = selected.includes(t.team_id);
                  return (
                    <TouchableOpacity
                      key={t.team_id}
                      onPress={() => toggle(t.team_id)}
                      style={[styles.teamItem, on && { backgroundColor: colors.field600 }]}
                    >
                      <View style={[styles.checkbox, on && styles.checkboxOn]}>
                        {on && <Text style={styles.checkmark}>✓</Text>}
                      </View>
                      <Text style={[styles.teamItemText, on && { color: colors.ink }]}>
                        {t.team_name}
                      </Text>
                    </TouchableOpacity>
                  );
                })}
              </View>
            )}
          </View>

          {error && <Text style={styles.errorText}>Submission failed: {error}</Text>}

          <TouchableOpacity
            onPress={submit}
            disabled={!canSubmit}
            style={[styles.submitBtn, canSubmit ? styles.submitOn : styles.submitOff]}
          >
            {submitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={[styles.submitText, { color: canSubmit ? '#fff' : colors.muteDim }]}>
                Spread the Rumor
              </Text>
            )}
          </TouchableOpacity>
          <View style={{ height: 16 }} />
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.field800,
  },
  content: {
    paddingVertical: 14,
    paddingHorizontal: 16,
    gap: 14,
  },
  infoBanner: {
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 13,
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
  },
  infoText: {
    flex: 1,
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.muted,
    lineHeight: 18,
  },
  infoStrong: {
    fontFamily: fontFamily.bodySemiBold,
    color: colors.silver,
  },
  fieldLabel: {
    fontFamily: fontFamily.mono,
    fontSize: 9,
    color: colors.muteDim,
    letterSpacing: 1.1,
    textTransform: 'uppercase',
    marginBottom: 7,
  },
  textarea: {
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 8,
    paddingVertical: 11,
    paddingHorizontal: 13,
    fontFamily: fontFamily.body,
    fontSize: 13,
    color: colors.ink,
    minHeight: 110,
    textAlignVertical: 'top',
    lineHeight: 20,
  },
  counter: {
    fontFamily: fontFamily.mono,
    fontSize: 9.5,
    color: colors.muteDim,
    textAlign: 'right',
    marginTop: 4,
  },
  tagToggle: {
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 8,
    paddingVertical: 11,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  tagToggleOpen: {
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
  },
  tagCount: {
    fontFamily: fontFamily.display,
    fontSize: 11,
    color: colors.gold,
    marginBottom: 7,
  },
  teamList: {
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderTopWidth: 0,
    borderColor: colors.stroke,
    borderBottomLeftRadius: 8,
    borderBottomRightRadius: 8,
    overflow: 'hidden',
  },
  teamItem: {
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 9,
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  checkbox: {
    width: 16,
    height: 16,
    borderRadius: 3,
    borderWidth: 1.5,
    borderColor: colors.stroke2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxOn: {
    borderColor: colors.gold,
    backgroundColor: colors.gold,
  },
  checkmark: {
    fontSize: 10,
    fontWeight: 'bold',
    color: colors.field900,
    lineHeight: 12,
  },
  teamItemText: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.silver,
  },
  errorText: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.red,
    textAlign: 'center',
  },
  submitBtn: {
    borderRadius: 8,
    borderWidth: 1,
    paddingVertical: 13,
    alignItems: 'center',
  },
  submitOn: {
    backgroundColor: colors.crimson,
    borderColor: colors.crimson,
  },
  submitOff: {
    backgroundColor: colors.field600,
    borderColor: colors.stroke,
  },
  submitText: {
    fontFamily: fontFamily.displayBold,
    fontSize: 15,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },

  // Done state
  doneWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
    gap: 16,
  },
  doneCircle: {
    width: 62,
    height: 62,
    borderRadius: 31,
    backgroundColor: '#14532d33',
    borderWidth: 2,
    borderColor: colors.green,
    alignItems: 'center',
    justifyContent: 'center',
  },
  doneTitle: {
    fontFamily: fontFamily.displayBold,
    fontSize: 20,
    color: colors.ink,
    textTransform: 'uppercase',
    letterSpacing: 1,
    textAlign: 'center',
  },
  doneBody: {
    fontFamily: fontFamily.body,
    fontSize: 13,
    color: colors.muted,
    textAlign: 'center',
    lineHeight: 20,
    maxWidth: 260,
  },
  againBtn: {
    marginTop: 8,
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.stroke2,
    borderRadius: 8,
    paddingVertical: 11,
    paddingHorizontal: 28,
  },
  againText: {
    fontFamily: fontFamily.display,
    fontSize: 14,
    color: colors.ink,
    letterSpacing: 1.4,
    textTransform: 'uppercase',
  },
});
