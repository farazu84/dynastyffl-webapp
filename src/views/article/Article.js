import { useLocation } from 'react-router-dom'
import ReactMarkdown from 'react-markdown';
import '../../styles/Article.css'


const Article = ( ) => {
    const location = useLocation()
    const { article } = location.state
    console.log(article)
    return (
        <div className="article-page">
            <div className="article-header">
                <h3>News</h3>
                {article.thumbnail && (
                    <img 
                        src={article.thumbnail} 
                        alt={article.title}
                        className="article-thumbnail"
                    />
                )}
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