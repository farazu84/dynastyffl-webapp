import React, { useCallback } from 'react';
import { Link } from 'react-router-dom';
import fallbackImage from '../../studio-gib-1.png';
import '../../styles/LatestNews.css';

const formatDate = (dateString) => {
    if (!dateString) return 'Recently';
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric', month: 'long', day: 'numeric',
    });
};

const CompactArticleCard = ({ article, showPublishedStatus = false }) => {
    const handleImageError = useCallback((e) => {
        e.target.src = fallbackImage;
    }, []);

    // Accept pre-processed fields from ArticleHeader or fall back to raw fields
    const imageSrc = article.imageSrc
        ?? (article.thumbnail?.trim() ? article.thumbnail : fallbackImage);
    const date = article.formattedDate ?? formatDate(article.creation_date);

    return (
        <Link
            to={article?.article_id ? `/articles/${article.article_id}` : '#'}
            state={{ article }}
            className={`compact-article-link ${!article?.article_id ? 'disabled' : ''}`}
        >
            <div className="compact-article">
                <div className="compact-image-container">
                    <img
                        src={imageSrc}
                        alt="League News"
                        className="compact-image"
                        onError={handleImageError}
                    />
                </div>
                <div className="compact-content">
                    <div className="compact-meta">
                        <span className="compact-author">{article?.author || 'League News'}</span>
                        <span className="compact-date">{date}</span>
                    </div>
                    <h4 className="compact-title">{article?.title || 'League News'}</h4>
                    {showPublishedStatus && (
                        <span className={`article-status-badge ${article?.published ? 'badge--published' : 'badge--draft'}`}>
                            {article?.published ? 'Published' : 'Draft'}
                        </span>
                    )}
                </div>
            </div>
        </Link>
    );
};

export default CompactArticleCard;
