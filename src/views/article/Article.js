import { useParams } from 'react-router-dom'
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import '../../styles/Article.css'
import fallbackImage from '../../studio-gib-1.png';


const Article = ( ) => {
    const { articleId } = useParams();
    const [article, setArticle] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [fetchError, setFetchError] = useState(null);

    useEffect(() => {
        const fetchArticle = async () => {
            try {
                const response = await fetch(`/articles/${articleId}`);
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

    const handleImageError = (e) => {
        e.target.src = fallbackImage;
    };

    const getImageSrc = (thumbnail) => {
        return thumbnail && thumbnail.trim() !== '' ? thumbnail : fallbackImage;
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
            <div className="article-header">
                <h3>News</h3>
                <h2>{article.title}</h2>
                <p className="article-meta">Author: {article.author}</p>
                <p className="article-meta">Published: {new Date(article.creation_date).toLocaleDateString()}</p>
            </div>
            <div className='article-content'>
                <ReactMarkdown>{article.content}</ReactMarkdown>
            </div>
        </div>
    )
}

export default Article