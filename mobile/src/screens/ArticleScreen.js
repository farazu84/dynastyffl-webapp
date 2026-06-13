import { ScrollView, View, Text, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Markdown from 'react-native-markdown-display';
import { colors, fontFamily, articleTypeColor, articleTypeLabel } from '../theme';
import AppHeader from '../components/AppHeader';
import { TypePill } from '../components/atoms';

const fmtDate = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });
};

export default function ArticleScreen({ route, navigation }) {
  const { article } = route.params;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <AppHeader title="Article" back onBack={() => navigation.goBack()} />
      <ScrollView contentContainerStyle={styles.content}>
        <TypePill
          label={articleTypeLabel(article.article_type)}
          acct={articleTypeColor(article.article_type)}
        />
        <Text style={styles.title}>{article.title}</Text>
        <Text style={styles.byline}>
          By {article.author}  ·  {fmtDate(article.creation_date)}
        </Text>
        <View style={styles.rule} />
        <Markdown style={markdownStyles}>{article.content ?? ''}</Markdown>
        <View style={{ height: 32 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.field800,
  },
  content: {
    padding: 16,
  },
  title: {
    fontFamily: fontFamily.displayBold,
    fontSize: 22,
    color: colors.ink,
    lineHeight: 28,
    marginTop: 10,
    marginBottom: 8,
  },
  byline: {
    fontFamily: fontFamily.body,
    fontSize: 12,
    color: colors.muted,
  },
  rule: {
    height: 1,
    backgroundColor: colors.hairline,
    marginVertical: 14,
  },
});

const markdownStyles = {
  body: {
    fontFamily: fontFamily.body,
    fontSize: 14,
    lineHeight: 22,
    color: colors.silver,
  },
  heading1: {
    fontFamily: fontFamily.display,
    fontSize: 20,
    lineHeight: 26,
    color: colors.ink,
    marginTop: 16,
    marginBottom: 8,
  },
  heading2: {
    fontFamily: fontFamily.display,
    fontSize: 17,
    lineHeight: 22,
    color: colors.ink,
    marginTop: 14,
    marginBottom: 6,
  },
  heading3: {
    fontFamily: fontFamily.display,
    fontSize: 15,
    lineHeight: 20,
    color: colors.gold,
    marginTop: 12,
    marginBottom: 4,
  },
  strong: {
    fontFamily: fontFamily.bodySemiBold,
    color: colors.ink,
  },
  em: {
    fontStyle: 'italic',
  },
  link: {
    color: colors.gold,
  },
  blockquote: {
    backgroundColor: colors.field700,
    borderLeftWidth: 3,
    borderLeftColor: colors.gold,
    paddingHorizontal: 12,
    paddingVertical: 4,
    marginVertical: 8,
  },
  code_inline: {
    fontFamily: fontFamily.mono,
    backgroundColor: colors.field900,
    color: colors.goldHi,
    fontSize: 13,
  },
  fence: {
    backgroundColor: colors.field900,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 6,
    padding: 12,
  },
  code_block: {
    fontFamily: fontFamily.mono,
    fontSize: 12,
    color: colors.silver,
  },
  hr: {
    backgroundColor: colors.stroke,
    marginVertical: 14,
  },
  bullet_list: {
    marginVertical: 6,
  },
  ordered_list: {
    marginVertical: 6,
  },
  table: {
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 4,
    marginVertical: 8,
  },
  th: {
    fontFamily: fontFamily.bodySemiBold,
    color: colors.ink,
    padding: 6,
    backgroundColor: colors.field700,
  },
  td: {
    padding: 6,
    borderColor: colors.stroke,
  },
};
