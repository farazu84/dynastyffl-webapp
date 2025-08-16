import './styles/Header.css';

const Header = () => {
    const handleNavigation = (path) => {
        window.location.href = path;
    };

    return (
        <header>
            <div className="header-container">
                <h1>LHS Fantasy Football League</h1>
                <nav className='header-menu'>
                    <button onClick={() => handleNavigation('/')}>Home</button>
                    <button>Teams</button>
                    <button>News</button>
                    <button onClick={() => handleNavigation('/rumors')}>Rumor Mill</button>
                </nav>
            </div>
        </header>
    )
}

export default Header