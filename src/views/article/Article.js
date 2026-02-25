import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';
import '../../styles/Article.css';

import config from '../../config';
import { useAuth } from '../../hooks/useAuth';
import { useAuthFetch } from '../../hooks/useAuthFetch';


const Article = ( ) => {
    const { articleId } = useParams();
    const { user } = useAuth();
    const authFetch = useAuthFetch();
    const [article, setArticle] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [fetchError, setFetchError] = useState(null);
    const [publishing, setPublishing] = useState(false);
    const [publishError, setPublishError] = useState(null);

    useEffect(() => {
        const fetchArticle = async () => {
            try {
                const response = await fetch(`${config.API_BASE_URL}/articles/${articleId}`);
                const data = await response.json();
                console.log(data);
                
                if (data.success && data.article) {
                    setArticle(data.article);
                } else {
                    setFetchError('Article not found');
                }
            } catch (error) {
                console.error('Error fetching article:', error);
                setFetchError(error.message);
            } finally {
                setIsLoading(false);
            }
        };

        if (articleId) {
            fetchArticle();
        }
    }, [articleId]);

    const handlePublish = async () => {
        setPublishing(true);
        setPublishError(null);
        try {
            const res = await authFetch(`/admin/articles/${articleId}/publish`, { method: 'POST' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to publish');
            setArticle(data.article);
        } catch (err) {
            setPublishError(err.message);
        } finally {
            setPublishing(false);
        }
    };

    if (isLoading) {
        return (
            <div className="article-page">
                <div className="article-header">
                    <div>Loading article...</div>
                </div>
            </div>
        );
    }

    if (fetchError) {
        return (
            <div className="article-page">
                <div className="article-header">
                    <div>Error loading article: {fetchError}</div>
                </div>
            </div>
        );
    }

    if (!article) {
        return (
            <div className="article-page">
                <div className="article-header">
                    <div>Article not found</div>
                </div>
            </div>
        );
    }

    return (
        <div className="article-page">
            {user?.admin && !article.published && (
                <div className="article-publish-bar">
                    <span className="article-draft-badge">Draft</span>
                    <button
                        className="article-publish-btn"
                        onClick={handlePublish}
                        disabled={publishing}
                    >
                        {publishing ? 'Publishing...' : 'Publish Article'}
                    </button>
                    {publishError && <span className="article-publish-error">{publishError}</span>}
                </div>
            )}
            <div className="article-header">
                <h3>News</h3>
                <h2>{article.title}</h2>
                <p className="article-meta">Author: {article.author}</p>
                <p className="article-meta">Published: {new Date(article.creation_date).toLocaleDateString()}</p>
            </div>
            <div className='article-content'>
                <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                >
                    {article.content}
                </ReactMarkdown>
            </div>
        </div>
    )
}

export default Article