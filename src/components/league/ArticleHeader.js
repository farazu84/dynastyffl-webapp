import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';


const ArticleHeader = () => {
    const [article, setArticle] = useState({});
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchArticle = async () => {
            try{
                const response = await fetch('articles/6');
                const articleJSON = await response.json()
                setArticle(articleJSON.article);
                setFetchError(null);
                console.log(article)
            } catch (error) {
                setFetchError(error.message)
            } finally {
                setIsLoading(false);
            }
        }
    
        fetchArticle()
    }, [])

    
    return (
        <>
            <h3>News</h3>
            <Link to={`/articles/${article.article_id}`} state={{ article: article }} >
                <img src={article.thumbnail} height='600px' width='600px'></img>
            </Link>
        </>
    )
}

export default ArticleHeader