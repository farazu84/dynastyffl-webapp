import { useLocation } from 'react-router-dom'
import parse from 'html-react-parser';
import '../../styles/Article.css'


const Article = ( ) => {
    const location = useLocation()
    const { article } = location.state
    console.log(article)
    return (
        <>
            <h3>News</h3>
            <img src={article.thumbnail} height='600px' width='600px'></img>
            <h2>{article.title}</h2>
            <p>Author: {article.author}</p>
            <p>Publish Date: {article.creation_date}</p>
            <div className='article-content'>
                {parse(article.content)}
            </div>
        </>
    )
}

export default Article