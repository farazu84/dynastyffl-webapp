import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import fallbackImage from '../../studio-gib-1.png';
import TrendingPlayers from './TrendingPlayers';
import '../../styles/LatestNews.css';
import config from '../../config';


const ArticleHeader = () => {
    const [articles, setArticles] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchArticles = async () => {
            try{
                const response = await fetch(`${config.API_BASE_URL}/articles/get_latest_articles`);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const articlesJSON = await response.json()
                console.log(articlesJSON)
                
                // Handle both single article and articles array responses
                let articlesList = [];
                if (articlesJSON?.articles && Array.isArray(articlesJSON.articles)) {
                    articlesList = articlesJSON.articles;
                } else if (articlesJSON?.article) {
                    articlesList = [articlesJSON.article];
                } else {
                    throw new Error('No article data received');
                }
                
                // Process and validate each article
                const processedArticles = articlesList.map(article => ({
                    title: article?.title || 'Latest League News',
                    author: article?.author || 'League News',
                    content: article?.content || '',
                    thumbnail: article?.thumbnail || '',
                    creation_date: article?.creation_date || '',
                    article_id: article?.article_id || null
                }));
                
                setArticles(processedArticles);
                setFetchError(null);
            } catch (error) {
                console.error('Error fetching articles:', error);
                setFetchError(error.message);
                // Set fallback article data
                setArticles([
                    {
                        title: 'Welcome to LHS Fantasy Football League',
                        author: 'League Commissioner',
                        content: 'Stay tuned for the latest league news and updates!',
                        thumbnail: '',
                        creation_date: new Date().toISOString(),
                        article_id: null
                    }
                ]);
            } finally {
                setIsLoading(false);
            }
        }
    
        fetchArticles()
    }, [])

    const handleImageError = (e) => {
        e.target.src = fallbackImage;
    };

    const getImageSrc = (article) => {
        return article?.thumbnail && article?.thumbnail.trim() !== '' ? article.thumbnail : fallbackImage;
    };
    
    const formatDate = (dateString) => {
        if (!dateString) return 'Recently';
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const renderFeaturedArticle = (article) => (
        <Link 
            to={article?.article_id ? `/articles/${article.article_id}` : '#'} 
            state={{ article: article }}
            className={`featured-article-link ${!article?.article_id ? 'disabled' : ''}`}
        >
            <div className="news-card featured">
                <div className="news-image-container">
                    <img 
                        src={getImageSrc(article)} 
                        alt={'League News'}
                        className="news-image"
                        onError={handleImageError}
                    />
                </div>
                <div className="news-content">
                    <div className="news-meta">
                        <span className="news-author">{article?.author || 'League News'}</span>
                        <span className="news-date">{formatDate(article?.creation_date)}</span>
                    </div>
                    <h3 className="news-title">{article?.title || 'Latest League News'}</h3>
                    <p className="news-excerpt">
                        {article?.content ? 
                            article.content.substring(0, 150) + (article.content.length > 150 ? '...' : '') 
                            : 'Click to read the full article'
                        }
                    </p>
                </div>
            </div>
        </Link>
    );

    const renderCompactArticle = (article, index) => (
        <Link 
            key={article.article_id || index}
            to={article?.article_id ? `/articles/${article.article_id}` : '#'} 
            state={{ article: article }}
            className={`compact-article-link ${!article?.article_id ? 'disabled' : ''}`}
        >
            <div className="compact-article">
                <div className="compact-image-container">
                    <img 
                        src={getImageSrc(article)} 
                        alt={'League News'}
                        className="compact-image"
                        onError={handleImageError}
                    />
                </div>
                <div className="compact-content">
                    <div className="compact-meta">
                        <span className="compact-author">{article?.author || 'League News'}</span>
                        <span className="compact-date">{formatDate(article?.creation_date)}</span>
                    </div>
                    <h4 className="compact-title">{article?.title || 'League News'}</h4>
                </div>
            </div>
        </Link>
    );

    if (isLoading) {
        return (
            <div className="latest-news-container">
                <h2 className="latest-news-title">Latest News</h2>
                <div className="news-card loading">
                    <div className="loading-text">Loading latest news...</div>
                </div>
            </div>
        );
    }
    
    return (
        <div className="news-and-trending-container">
            <div className="latest-news-container">
                <h2 className="latest-news-title">Latest News</h2>
                <div className="news-feed">
                    {articles.length > 0 ? (
                        <>
                            {/* Featured Article - Latest/First Article */}
                            {renderFeaturedArticle(articles[0])}
                            
                            {/* Compact Articles - Remaining Articles (Max 4) */}
                            {articles.length > 1 && (
                                <div className="compact-articles-section">
                                    <div className="compact-articles-grid">
                                        {articles.slice(1, 5).map((article, index) => 
                                            renderCompactArticle(article, index + 1)
                                        )}
                                    </div>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="news-card">
                            <div className="news-content">
                                <h3 className="news-title">No Articles Available</h3>
                                <p className="news-excerpt">Check back later for the latest league news and updates!</p>
                            </div>
                        </div>
                    )}
                </div>
                {fetchError && (
                    <div className="error-message">
                        Unable to load latest news. {fetchError}
                    </div>
                )}
            </div>
            <div className="trending-players-wrapper">
                <div className="trending-players-title-spacer"></div>
                <TrendingPlayers />
            </div>
        </div>
    )
}

export default ArticleHeader