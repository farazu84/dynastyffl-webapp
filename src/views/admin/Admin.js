import React, { useState, useEffect } from 'react';
import { useAuthFetch } from '../../hooks/useAuthFetch';
import CompactArticleCard from '../../components/articles/CompactArticleCard';
import './Admin.css';

const Admin = () => {
    const authFetch = useAuthFetch();
    const [articles, setArticles] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchUnpublished = async () => {
            try {
                const res = await authFetch('/admin/articles/unpublished');
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                const data = await res.json();
                setArticles(data.articles.slice(0, 5));
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchUnpublished();
    }, [authFetch]);

    return (
        <div className="admin-container">
            <section className="admin-section">
                <h2 className="admin-section-title">Unpublished Articles</h2>

                {isLoading && <p className="admin-status">Loading...</p>}
                {error && <p className="admin-error">{error}</p>}

                {!isLoading && !error && articles.length === 0 && (
                    <p className="admin-status">No unpublished articles.</p>
                )}

                {articles.length > 0 && (
                    <div className="admin-articles-grid">
                        {articles.map(article => (
                            <CompactArticleCard
                                key={article.article_id}
                                article={article}
                                showPublishedStatus={true}
                            />
                        ))}
                    </div>
                )}
            </section>
        </div>
    );
};

export default Admin;
