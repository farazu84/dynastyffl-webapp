import { Link } from 'react-router-dom';
import '../../styles/NewsBar.css';

const NewsBar = ({ articles }) => {
    // Take the first 4 articles from the passed articles array
    const teamNews = articles ? articles.slice(0, 4) : [];
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric'
        });
    };

    const getArticleTypeLabel = (type) => {
        const typeLabels = {
            'power_ranking': 'Rankings',
            'team_analysis': 'Analysis',
            'rumors': 'Rumors',
            'trade_analysis': 'Trades',
            'injury': 'Injury',
            'matchup_analysis': 'Matchup',
            'matchup_breakdown': 'Preview'
        };
        return typeLabels[type] || 'News';
    };

    const truncateTitle = (title, maxLength = 60) => {
        if (!title) return 'Untitled';
        return title.length > maxLength 
            ? title.substring(0, maxLength) + '...'
            : title;
    };

    if (teamNews.length === 0) {
        return (
            <div className="news-bar">
                <div className="news-bar-header">
                    <h3>Latest Team News</h3>
                </div>
                <div className="news-bar-content">
                    <div className="no-news">No recent news available</div>
                </div>
            </div>
        );
    }

    return (
        <div className="news-bar">
            <div className="news-bar-header">
                <h3>Latest Team News</h3>
                <Link to="/news" className="view-all-link">View All</Link>
            </div>
            <div className="news-bar-content">
                <div className="news-items">
                    {teamNews.map(article => (
                        <Link 
                            key={article.article_id} 
                            to={`/articles/${article.article_id}`} 
                            className="news-item-link"
                        >
                            <div className="news-item">
                                <div className="news-item-badge">
                                    {getArticleTypeLabel(article.article_type)}
                                </div>
                                <div className="news-item-content">
                                    <h4 className="news-item-title">
                                        {truncateTitle(article.title)}
                                    </h4>
                                    <div className="news-item-meta">
                                        <span className="news-item-author">By {article.author}</span>
                                        <span className="news-item-date">{formatDate(article.creation_date)}</span>
                                    </div>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default NewsBar;
