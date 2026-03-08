import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthFetch } from '../../hooks/useAuthFetch';
import { useAuth } from '../../hooks/useAuth';
import CompactArticleCard from '../../components/articles/CompactArticleCard';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import './Admin.css';

const currentYear = new Date().getFullYear();
const toMidnightISO = (date) => {
    const d = new Date(date);
    d.setHours(0, 0, 0, 0);
    return d.toISOString();
};

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

    // UDFA — Bidding Window
    const [opensAt, setOpensAt] = useState(new Date());
    const [closesAt, setClosesAt] = useState(new Date());
    const [windowStatus, setWindowStatus] = useState(null);
    const [windowError, setWindowError] = useState(null);
    const [settingWindow, setSettingWindow] = useState(false);

    // UDFA — Seed Budgets
    const [budgetStatus, setBudgetStatus] = useState(null);
    const [budgetError, setBudgetError] = useState(null);
    const [seedingBudgets, setSeedingBudgets] = useState(false);

    // UDFA — Process Bids
    const [processResults, setProcessResults] = useState(null);
    const [processError, setProcessError] = useState(null);
    const [processing, setProcessing] = useState(false);

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

    const handleSetWindow = useCallback(async () => {
        setSettingWindow(true);
        setWindowStatus(null);
        setWindowError(null);
        try {
            const res = await authFetch('/admin/udfa/window', {
                method: 'POST',
                body: JSON.stringify({ year: currentYear, opens_at: toMidnightISO(opensAt), closes_at: toMidnightISO(closesAt) }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to set window');
            setWindowStatus(`Window set: opens ${new Date(data.window.opens_at).toLocaleDateString()}, closes ${new Date(data.window.closes_at).toLocaleDateString()}`);
        } catch (err) {
            setWindowError(err.message);
        } finally {
            setSettingWindow(false);
        }
    }, [authFetch, opensAt, closesAt]);

    const handleSeedBudgets = useCallback(async () => {
        setSeedingBudgets(true);
        setBudgetStatus(null);
        setBudgetError(null);
        try {
            const res = await authFetch('/admin/udfa/budgets', {
                method: 'POST',
                body: JSON.stringify({ year: currentYear }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to seed budgets');
            setBudgetStatus(`Seeded ${data.budgets.length} team budget(s) for ${currentYear}.`);
        } catch (err) {
            setBudgetError(err.message);
        } finally {
            setSeedingBudgets(false);
        }
    }, [authFetch]);

    const handleProcessBids = useCallback(async () => {
        if (!window.confirm(`Process all UDFA bids for ${currentYear}? This cannot be undone.`)) return;
        setProcessing(true);
        setProcessResults(null);
        setProcessError(null);
        try {
            const res = await authFetch('/admin/udfa/process', {
                method: 'POST',
                body: JSON.stringify({ year: currentYear }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to process bids');
            setProcessResults(data.results);
        } catch (err) {
            setProcessError(err.message);
        } finally {
            setProcessing(false);
        }
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
                <h2 className="admin-section-title">UDFA Management</h2>

                {/* Set Bidding Window */}
                <div className="admin-udfa-block">
                    <h3 className="admin-udfa-block-title">Set Bidding Window</h3>
                    <div className="admin-udfa-row">
                        <div className="admin-datepicker-wrap">
                            <label className="admin-datepicker-label">Opens</label>
                            <DatePicker
                                selected={opensAt}
                                onChange={setOpensAt}
                                dateFormat="MMM d, yyyy"
                                className="admin-input admin-datepicker-input"
                                popperClassName="admin-datepicker-popper"
                            />
                        </div>
                        <div className="admin-datepicker-wrap">
                            <label className="admin-datepicker-label">Closes</label>
                            <DatePicker
                                selected={closesAt}
                                onChange={setClosesAt}
                                dateFormat="MMM d, yyyy"
                                minDate={opensAt}
                                className="admin-input admin-datepicker-input"
                                popperClassName="admin-datepicker-popper"
                            />
                        </div>
                        <button className="admin-action-btn" onClick={handleSetWindow} disabled={settingWindow || !opensAt || !closesAt}>
                            {settingWindow ? 'Saving...' : 'Set Window'}
                        </button>
                    </div>
                    {windowStatus && <p className="admin-udfa-success">{windowStatus}</p>}
                    {windowError && <p className="admin-error">{windowError}</p>}
                </div>

                {/* Seed Budgets */}
                <div className="admin-udfa-block">
                    <h3 className="admin-udfa-block-title">Seed Team Budgets</h3>
                    <div className="admin-udfa-row">
                        <button className="admin-action-btn" onClick={handleSeedBudgets} disabled={seedingBudgets}>
                            {seedingBudgets ? 'Seeding...' : 'Seed Budgets'}
                        </button>
                    </div>
                    {budgetStatus && <p className="admin-udfa-success">{budgetStatus}</p>}
                    {budgetError && <p className="admin-error">{budgetError}</p>}
                </div>

                {/* Process Bids */}
                <div className="admin-udfa-block admin-udfa-block--danger">
                    <h3 className="admin-udfa-block-title">Process Bids</h3>
                    <p className="admin-udfa-block-desc">Settles all pending bids for the year. Highest bid wins; ties broken by waiver order. <strong>Irreversible.</strong></p>
                    <div className="admin-udfa-row">
                        <button className="admin-action-btn admin-action-btn--danger" onClick={handleProcessBids} disabled={processing}>
                            {processing ? 'Processing...' : 'Process Bids'}
                        </button>
                    </div>
                    {processError && <p className="admin-error">{processError}</p>}
                    {processResults && (
                        <div className="admin-process-results">
                            <p className="admin-udfa-success">{processResults.length} player(s) settled.</p>
                            <div className="admin-process-results-list">
                                {processResults.map(r => (
                                    <div key={r.player_sleeper_id} className="admin-process-result-row">
                                        <span className="admin-process-result-team">{r.winner_team_name}</span>
                                        <span className="admin-process-result-amount">${r.winning_amount}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
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
