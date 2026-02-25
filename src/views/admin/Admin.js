import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthFetch } from '../../hooks/useAuthFetch';
import { useAuth } from '../../hooks/useAuth';
import CompactArticleCard from '../../components/articles/CompactArticleCard';
import './Admin.css';

const Admin = () => {
    const authFetch = useAuthFetch();
    const { impersonate } = useAuth();
    const navigate = useNavigate();

    const [articles, setArticles] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    const [teamOwners, setTeamOwners] = useState([]);
    const [selectedUserId, setSelectedUserId] = useState('');
    const [impersonating, setImpersonating] = useState(false);
    const [impersonateError, setImpersonateError] = useState(null);

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

    useEffect(() => {
        const fetchOwners = async () => {
            try {
                const res = await authFetch('/admin/team-owners');
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                const data = await res.json();
                setTeamOwners(data.users);
            } catch (err) {
                setImpersonateError(err.message);
            }
        };
        fetchOwners();
    }, [authFetch]);

    const handleImpersonate = useCallback(async () => {
        if (!selectedUserId) return;
        setImpersonating(true);
        setImpersonateError(null);
        try {
            const res = await authFetch(`/admin/impersonate/${selectedUserId}`, { method: 'POST' });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.error || `HTTP error! status: ${res.status}`);
            }
            const { access_token, user } = await res.json();
            impersonate(access_token, user);
            navigate('/');
        } catch (err) {
            setImpersonateError(err.message);
            setImpersonating(false);
        }
    }, [selectedUserId, authFetch, impersonate, navigate]);

    return (
        <div className="admin-container">
            <section className="admin-section">
                <h2 className="admin-section-title">Impersonate Account</h2>
                <div className="admin-impersonate-row">
                    <select
                        className="admin-select"
                        value={selectedUserId}
                        onChange={e => setSelectedUserId(e.target.value)}
                    >
                        <option value="">Select a team owner...</option>
                        {teamOwners.map(u => (
                            <option key={u.user_id} value={u.user_id}>
                                {u.user_name}{u.first_name || u.last_name ? ` (${[u.first_name, u.last_name].filter(Boolean).join(' ')})` : ''}
                            </option>
                        ))}
                    </select>
                    <button
                        className="admin-impersonate-btn"
                        onClick={handleImpersonate}
                        disabled={!selectedUserId || impersonating}
                    >
                        {impersonating ? 'Impersonating...' : 'Impersonate'}
                    </button>
                </div>
                {impersonateError && <p className="admin-error">{impersonateError}</p>}
            </section>

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
