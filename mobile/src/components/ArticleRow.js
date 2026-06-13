import { View, Text, TouchableOpacity, Image, StyleSheet } from 'react-native';
import { colors, fontFamily, articleTypeColor, articleTypeLabel } from '../theme';
import { TypePill } from './atoms';
import { IcNews } from './icons';

const fmtDate = (iso) => {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const ArticleRow = ({ article, index, onPress }) => {
  const acct = articleTypeColor(article.article_type);
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[styles.row, { backgroundColor: index % 2 === 0 ? colors.field800 : colors.field900 }]}
    >
      {article.thumbnail ? (
        <Image source={{ uri: article.thumbnail }} style={styles.thumb} resizeMode="cover" />
      ) : (
        <View style={[styles.thumb, styles.thumbFallback, { borderColor: acct + '33' }]}>
          <IcNews c="rgba(255,255,255,0.35)" s={22} />
        </View>
      )}
      <View style={styles.info}>
        <View style={{ marginBottom: 5 }}>
          <TypePill label={articleTypeLabel(article.article_type)} acct={acct} />
        </View>
        <Text style={styles.title} numberOfLines={2}>{article.title}</Text>
        <Text style={styles.byline}>
          {article.author}  ·  {fmtDate(article.creation_date)}
        </Text>
      </View>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  row: {
    borderBottomWidth: 1,
    borderBottomColor: colors.stroke,
    paddingVertical: 12,
    paddingHorizontal: 16,
    flexDirection: 'row',
    gap: 12,
    alignItems: 'flex-start',
  },
  thumb: {
    width: 52,
    height: 52,
    borderRadius: 7,
  },
  thumbFallback: {
    backgroundColor: colors.field600,
    borderWidth: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  info: {
    flex: 1,
    minWidth: 0,
  },
  title: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
    lineHeight: 17,
    marginBottom: 5,
  },
  byline: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    color: colors.muteDim,
  },
});

export default ArticleRow;
