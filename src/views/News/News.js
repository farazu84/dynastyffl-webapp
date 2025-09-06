import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import '../../styles/News.css';
import fallbackImage from '../../studio-gib-1.png';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';

const News = React.memo(() => {
    const [articles, setArticles] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchNews = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);
                
                const response = await cachedFetch(`${config.API_BASE_URL}/articles/get_news`);
                const data = await response.json();
                
                if (data.success && data.articles) {
                    // Process articles with fallback values
                    const processedArticles = data.articles.map(article => ({
                        ...article,
                        title: article.title || 'Untitled Article',
                        author: article.author || 'Anonymous',
                        creation_date: article.creation_date || new Date().toISOString(),
                        thumbnail: article.thumbnail || '',
                        content: article.content || '',
                        article_type: article.article_type || 'general'
                    }));
                    setArticles(processedArticles);
                } else {
                    setArticles([]);
                }
                setFetchError(null);
            } catch (error) {
                console.error('Error fetching news:', error);
                setFetchError(error.message);
                setArticles([]);
            } finally {
                setIsLoading(false);
            }
        };
    
        fetchNews();
    }, []);

    const handleImageError = useCallback((e) => {
        e.target.src = fallbackImage;
    }, []);

    const getImageSrc = useCallback((thumbnail) => {
        return thumbnail && thumbnail.trim() !== '' ? thumbnail : fallbackImage;
    }, []);

    const formatDate = useCallback((dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }, []);

    const getArticleTypeLabel = useCallback((type) => {
        const typeLabels = {
            'power_ranking': 'Power Rankings',
            'team_analysis': 'Team Analysis',
            'rumors': 'Rumors',
            'trade_analysis': 'Trade Analysis',
            'injury': 'Injury Report',
            'matchup_analysis': 'Matchup Analysis',
            'matchup_breakdown': 'Matchup Breakdown'
        };
        return typeLabels[type] || 'News';
    }, []);

    const truncateContent = useCallback((content, maxLength = 150) => {
        if (!content) return '';
        const plainText = content.replace(/[#*`]/g, '').replace(/\n/g, ' ');
        return plainText.length > maxLength 
            ? plainText.substring(0, maxLength) + '...'
            : plainText;
    }, []);

    // Memoize processed articles with all computed values
    const processedArticles = useMemo(() => {
        return articles.map(article => ({
            ...article,
            formattedDate: formatDate(article.creation_date),
            imageSrc: getImageSrc(article.thumbnail),
            typeLabel: getArticleTypeLabel(article.article_type),
            excerpt: truncateContent(article.content),
            featuredExcerpt: truncateContent(article.content, 200)
        }));
    }, [articles, formatDate, getImageSrc, getArticleTypeLabel, truncateContent]);

    // Memoize article splits to prevent recalculation
    const { featuredArticle, regularArticles } = useMemo(() => {
        if (processedArticles.length === 0) return { featuredArticle: null, regularArticles: [] };
        return {
            featuredArticle: processedArticles[0],
            regularArticles: processedArticles.slice(1)
        };
    }, [processedArticles]);

    if (isLoading) {
        return (
            <div className="news-page">
                <div className="news-container">
                    <div className="loading-message">Loading latest news...</div>
                </div>
            </div>
        );
    }

    if (fetchError) {
        return (
            <div className="news-page">
                <div className="news-container">
                    <div className="error-message">Error loading news: {fetchError}</div>
                </div>
            </div>
        );
    }

    if (processedArticles.length === 0 && !isLoading) {
        return (
            <div className="news-page">
                <div className="news-container">
                    <div className="no-articles">No articles available at this time.</div>
                </div>
            </div>
        );
    }

    return (
        <div className="news-page">
            <div className="news-container">
                
                <div className="news-grid">
                    {/* Featured Article */}
                    {featuredArticle && (
                        <div className="featured-section">
                            <Link to={`/articles/${featuredArticle.article_id}`} className="featured-article-link">
                                <article className="featured-article">
                                    <div className="featured-image-container">
                                        <img 
                                            src={featuredArticle.imageSrc} 
                                            alt={featuredArticle.title}
                                            className="featured-image"
                                            onError={handleImageError}
                                        />
                                        <div className="article-type-badge featured-badge">
                                            {featuredArticle.typeLabel}
                                        </div>
                                    </div>
                                    <div className="featured-content">
                                        <h2 className="featured-title">{featuredArticle.title}</h2>
                                        <div className="featured-meta">
                                            <span className="featured-author">By {featuredArticle.author}</span>
                                            <span className="featured-date">{featuredArticle.formattedDate}</span>
                                        </div>
                                        <p className="featured-excerpt">
                                            {featuredArticle.featuredExcerpt}
                                        </p>
                                    </div>
                                </article>
                            </Link>
                        </div>
                    )}

                    {/* Regular Articles Grid */}
                    <div className="articles-grid">
                        {regularArticles.map(article => (
                            <Link 
                                key={article.article_id} 
                                to={`/articles/${article.article_id}`} 
                                className="article-link"
                            >
                                <article className="news-article">
                                    <div className="article-image-container">
                                        <img 
                                            src={article.imageSrc} 
                                            alt={article.title}
                                            className="article-image"
                                            onError={handleImageError}
                                        />
                                        <div className="article-type-badge">
                                            {article.typeLabel}
                                        </div>
                                    </div>
                                    <div className="article-content">
                                        <h3 className="article-title">{article.title}</h3>
                                        <div className="article-meta">
                                            <span className="article-author">By {article.author}</span>
                                            <span className="article-date">{article.formattedDate}</span>
                                        </div>
                                        <p className="article-excerpt">
                                            {article.excerpt}
                                        </p>
                                    </div>
                                </article>
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
});

News.displayName = 'News';

export default News;