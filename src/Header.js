import { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './styles/Header.css';
import { useAuth } from './hooks/useAuth';
import LoginModal from './components/LoginModal';

const UserIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
        <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
    </svg>
);

const Header = () => {
    const { user, logout } = useAuth();
    const [showModal, setShowModal] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);
    const dropdownRef = useRef(null);

    // Close dropdown when clicking outside
    useEffect(() => {
        const handler = (e) => {
            if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
                setShowDropdown(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    const initials = user
        ? `${user.first_name?.[0] ?? ''}${user.last_name?.[0] ?? ''}`.toUpperCase() || user.user_name?.[0]?.toUpperCase()
        : null;

    return (
        <>
            <header>
                <div className="header-container">
                    <h1>LHS Fantasy Football League</h1>
                    <nav className='header-menu'>
                        <Link to="/">Home</Link>
                        <Link to="/news">News</Link>
                        <Link to="/archive">Archive</Link>
                        <Link to="/rumors">Rumor Mill</Link>
                        {user?.admin && <Link to="/admin" className="admin-link">Admin</Link>}
                    </nav>
                    <div className="header-auth">
                        {user ? (
                            <div className="auth-avatar" ref={dropdownRef}>
                                <button
                                    className="avatar-btn"
                                    onClick={() => setShowDropdown(v => !v)}
                                    title={user.user_name}
                                >
                                    {initials}
                                </button>
                                {showDropdown && (
                                    <div className="avatar-dropdown">
                                        <span className="dropdown-name">{user.first_name || user.user_name}</span>
                                        <button onClick={() => { logout(); setShowDropdown(false); }}>
                                            Sign out
                                        </button>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <button className="auth-icon-btn" onClick={() => setShowModal(true)} title="Sign in">
                                <UserIcon />
                            </button>
                        )}
                    </div>
                </div>
            </header>
            {showModal && <LoginModal onClose={() => setShowModal(false)} />}
        </>
    );
}

export default Header