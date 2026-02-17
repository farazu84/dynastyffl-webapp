import { Link } from 'react-router-dom';
import './styles/Header.css';

const Header = () => {
    return (
        <header>
            <div className="header-container">
                <h1>LHS Fantasy Football League</h1>
                <nav className='header-menu'>
                    <Link to="/">Home</Link>
                    <Link to="/news">News</Link>
                    <Link to="/archive">Archive</Link>
                    <Link to="/rumors">Rumor Mill</Link>
                </nav>
            </div>
        </header>
    )
}

export default Header