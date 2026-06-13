import { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
  Image,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, fontFamily, articleTypeColor, articleTypeLabel } from '../theme';
import { apiGet } from '../api';
import AppHeader from '../components/AppHeader';
import SectionHeader from '../components/SectionHeader';
import ArticleRow from '../components/ArticleRow';
import { TypePill } from '../components/atoms';

const fmtDate = (iso) => {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

export default function NewsScreen({ navigation }) {
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const fetchNews = useCallback(async () => {
    try {
      setError(null);
      const res = await apiGet('/articles/get_news');
      setArticles(res.articles ?? []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchNews(); }, [fetchNews]);

  const [featured, ...rest] = articles;
  const openArticle = (article) => navigation.navigate('Article', { article });

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <AppHeader title="News" />
      {loading ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color={colors.gold} />
        </View>
      ) : error ? (
        <View style={styles.centered}>
          <Text style={styles.errorText}>Error loading news: {error}</Text>
          <TouchableOpacity onPress={fetchNews} style={styles.retryBtn}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <ScrollView
          refreshControl={
            <RefreshControl
              refreshing={refreshing}
              onRefresh={() => { setRefreshing(true); fetchNews(); }}
              tintColor={colors.gold}
            />
          }
        >
          {featured && (
            <TouchableOpacity style={styles.featured} onPress={() => openArticle(featured)}>
              <View style={styles.featuredHero}>
                {featured.thumbnail ? (
                  <Image source={{ uri: featured.thumbnail }} style={styles.featuredImage} resizeMode="cover" />
                ) : (
                  <Text style={styles.featuredWatermark}>408</Text>
                )}
                <View style={styles.featuredPill}>
                  <TypePill
                    label={articleTypeLabel(featured.article_type)}
                    acct={articleTypeColor(featured.article_type)}
                  />
                </View>
              </View>
              <View style={styles.featuredBody}>
                <Text style={styles.featuredTitle}>{featured.title}</Text>
                <Text style={styles.byline}>
                  By {featured.author}  ·  {fmtDate(featured.creation_date)}
                </Text>
              </View>
            </TouchableOpacity>
          )}

          <SectionHeader label="Recent Articles" />
          {rest.map((a, i) => (
            <ArticleRow key={a.article_id} article={a} index={i} onPress={() => openArticle(a)} />
          ))}
          {articles.length === 0 && (
            <View style={styles.centered}>
              <Text style={styles.emptyText}>No articles yet</Text>
            </View>
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
    borderRadius: 4,
    paddingVertical: 8,
    paddingHorizontal: 20,
  },
  retryText: {
    fontFamily: fontFamily.bodySemiBold,
    fontSize: 13,
    color: colors.ink,
  },
  emptyText: {
    fontFamily: fontFamily.mono,
    fontSize: 11,
    color: colors.muteDim,
  },

  // Featured card
  featured: {
    margin: 14,
    marginHorizontal: 16,
    backgroundColor: colors.field700,
    borderWidth: 1,
    borderColor: colors.stroke,
    borderRadius: 10,
    overflow: 'hidden',
  },
  featuredHero: {
    height: 128,
    backgroundColor: colors.field600,
    alignItems: 'center',
    justifyContent: 'center',
  },
  featuredImage: {
    ...StyleSheet.absoluteFillObject,
  },
  featuredWatermark: {
    fontFamily: fontFamily.displayBold,
    fontSize: 72,
    color: 'rgba(255,255,255,0.06)',
    letterSpacing: 4,
  },
  featuredPill: {
    position: 'absolute',
    top: 10,
    left: 12,
  },
  featuredBody: {
    paddingHorizontal: 14,
    paddingTop: 12,
    paddingBottom: 14,
  },
  featuredTitle: {
    fontFamily: fontFamily.display,
    fontSize: 17,
    color: colors.ink,
    lineHeight: 22,
    marginBottom: 7,
  },
  byline: {
    fontFamily: fontFamily.body,
    fontSize: 11,
    color: colors.muted,
  },

});
