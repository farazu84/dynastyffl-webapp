import { Link } from 'react-router-dom';


const Header = () => {
    return (
        <header>
            <h1>LHS Fantasy Football League</h1>
            <div className='header-menu'>
                <button>Home</button>
                <button>Teams</button>
                <button>News</button>
            </div>
        </header>
    )
}

export default Header