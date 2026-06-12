import { Link } from 'react-router-dom';
import '../../styles/NewsBar.css';

const TYPE_LABELS = {
    power_ranking:      'Rankings',
    team_analysis:      'Analysis',
    rumors:             'Rumors',
    trade_analysis:     'Trades',
    injury:             'Injury',
    matchup_analysis:   'Matchup',
    matchup_breakdown:  'Preview',
};

const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const NewsBar = ({ articles }) => {
    const items = articles ? articles.slice(0, 4) : [];

    if (items.length === 0) {
        return (
            <div className="nb-bar">
                <div className="nb-label">
                    <div className="nb-live">
                        <span className="nb-live-dot" />
                        Live · Wire
                    </div>
                    <span className="nb-heading">Team News</span>
                </div>
                <div className="nb-empty">No recent news</div>
            </div>
        );
    }

    return (
        <div className="nb-bar">
            {/* Left label */}
            <div className="nb-label">
                <div className="nb-live">
                    <span className="nb-live-dot" />
                    Live · Wire
                </div>
                <span className="nb-heading">Team News</span>
            </div>

            {/* Articles */}
            <div className="nb-items">
                {items.map(article => (
                    <Link
                        key={article.article_id}
                        to={`/articles/${article.article_id}`}
                        className="nb-item-link"
                    >
                        <div className="nb-item">
                            <span className="nb-badge">
                                {TYPE_LABELS[article.article_type] ?? 'News'}
                            </span>
                            <span className="nb-title">{article.title}</span>
                            <span className="nb-meta">
                                {article.author} · {formatDate(article.creation_date)}
                            </span>
                        </div>
                    </Link>
                ))}
            </div>

            {/* View all */}
            <Link to="/news" className="nb-view-all">
                View All →
            </Link>
        </div>
    );
};

export default NewsBar;
