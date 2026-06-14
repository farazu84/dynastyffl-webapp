import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthFetch } from '../../hooks/useAuthFetch';
import { useAuth } from '../../hooks/useAuth';
import CompactArticleCard from '../../components/articles/CompactArticleCard';
import './Admin.css';

const currentYear = new Date().getFullYear();
const today = new Date().toISOString().split('T')[0];
const toMidnightISO = (dateStr) => new Date(dateStr).toISOString();

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
    const [opensAt, setOpensAt] = useState(today);
    const [closesAt, setClosesAt] = useState(today);
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

    // Data Sync & Backfill
    const [syncBusy, setSyncBusy] = useState(null); // which sync type is running
    const [syncMessage, setSyncMessage] = useState(null);
    const [syncError, setSyncError] = useState(null);
    const [backfillDataset, setBackfillDataset] = useState('playoffs');
    const [backfillYear, setBackfillYear] = useState('');
    const [backfillMessage, setBackfillMessage] = useState(null);
    const [backfillError, setBackfillError] = useState(null);
    const [syncStatus, setSyncStatus] = useState(null);

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

    const fetchSyncStatus = useCallback(async () => {
        try {
            const res = await authFetch('/admin/sync/status');
            if (!res.ok) return;
            const data = await res.json();
            setSyncStatus(data);
        } catch {
            /* transient; ignore */
        }
    }, [authFetch]);

    // Fetch once on mount (and page refresh). The sync/backfill actions below
    // refetch after they run, so the panel stays current without polling.
    useEffect(() => {
        fetchSyncStatus();
    }, [fetchSyncStatus]);

    // Poll only while a backfill is running, so its progress advances live;
    // the interval clears as soon as it finishes (running flips to false).
    useEffect(() => {
        if (!syncStatus?.backfill?.running) return;
        const id = setInterval(fetchSyncStatus, 5000);
        return () => clearInterval(id);
    }, [syncStatus?.backfill?.running, fetchSyncStatus]);

    const handleManualSync = useCallback(async (type) => {
        setSyncBusy(type);
        setSyncMessage(null);
        setSyncError(null);
        try {
            const res = await authFetch('/admin/sync', {
                method: 'POST',
                body: JSON.stringify({ type }),
            });
            const data = await res.json();
            const resultOk = data?.result?.success ?? data?.result?.overall_success ?? true;
            if (!res.ok || !resultOk) throw new Error(data.error || data?.result?.message || 'Sync failed');
            setSyncMessage(data.message || `${type} sync completed.`);
            fetchSyncStatus();
        } catch (err) {
            setSyncError(err.message);
        } finally {
            setSyncBusy(null);
        }
    }, [authFetch, fetchSyncStatus]);

    const handleBackfill = useCallback(async () => {
        if (!window.confirm(`Start "${backfillDataset}" backfill${backfillYear ? ` for ${backfillYear}` : ' (all seasons)'}? This hits the Sleeper API and can take minutes.`)) return;
        setBackfillMessage(null);
        setBackfillError(null);
        try {
            const body = { dataset: backfillDataset };
            if (backfillYear) body.year = Number(backfillYear);
            const res = await authFetch('/admin/backfill', {
                method: 'POST',
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Backfill failed to start');
            setBackfillMessage(data.message || 'Backfill started. Watch the status panel below.');
            fetchSyncStatus();
        } catch (err) {
            setBackfillError(err.message);
        }
    }, [authFetch, backfillDataset, backfillYear, fetchSyncStatus]);

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
                            <input
                                type="date"
                                className="admin-input"
                                value={opensAt}
                                onChange={e => setOpensAt(e.target.value)}
                            />
                        </div>
                        <div className="admin-datepicker-wrap">
                            <label className="admin-datepicker-label">Closes</label>
                            <input
                                type="date"
                                className="admin-input"
                                value={closesAt}
                                min={opensAt}
                                onChange={e => setClosesAt(e.target.value)}
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
                <h2 className="admin-section-title">Data Sync &amp; Backfill</h2>

                {/* Manual (current-week) syncs */}
                <div className="admin-udfa-block">
                    <h3 className="admin-udfa-block-title">Manual Sync</h3>
                    <p className="admin-udfa-block-desc">Pulls the current week from Sleeper. Fast; runs immediately.</p>
                    <div className="admin-udfa-row">
                        {['full', 'teams', 'matchups', 'players', 'transactions', 'player_stats', 'league_state'].map(t => (
                            <button
                                key={t}
                                className="admin-action-btn"
                                onClick={() => handleManualSync(t)}
                                disabled={syncBusy !== null}
                            >
                                {syncBusy === t ? 'Running…' : t.replace('_', ' ')}
                            </button>
                        ))}
                    </div>
                    {syncMessage && <p className="admin-udfa-success">{syncMessage}</p>}
                    {syncError && <p className="admin-error">{syncError}</p>}
                </div>

                {/* Historical backfill */}
                <div className="admin-udfa-block admin-udfa-block--danger">
                    <h3 className="admin-udfa-block-title">Historical Backfill</h3>
                    <p className="admin-udfa-block-desc">
                        Walks all seasons (or one) from Sleeper. Runs in the background and is safe to re-run.
                        Leave year blank for all seasons.
                    </p>
                    <div className="admin-udfa-row">
                        <select
                            className="admin-select"
                            value={backfillDataset}
                            onChange={e => setBackfillDataset(e.target.value)}
                        >
                            <option value="playoffs">Playoffs (brackets + championships)</option>
                            <option value="matchups">Matchups</option>
                            <option value="player_stats">Player stats</option>
                            <option value="draft_picks">Draft picks</option>
                            <option value="transactions">Transactions</option>
                            <option value="all">All datasets</option>
                        </select>
                        <input
                            type="number"
                            className="admin-input"
                            placeholder="Year (optional)"
                            value={backfillYear}
                            onChange={e => setBackfillYear(e.target.value)}
                        />
                        <button
                            className="admin-action-btn admin-action-btn--danger"
                            onClick={handleBackfill}
                            disabled={syncStatus?.backfill?.running}
                        >
                            {syncStatus?.backfill?.running ? 'Backfill running…' : 'Run Backfill'}
                        </button>
                    </div>
                    {backfillMessage && <p className="admin-udfa-success">{backfillMessage}</p>}
                    {backfillError && <p className="admin-error">{backfillError}</p>}
                </div>

                {/* Status panel */}
                <div className="admin-udfa-block">
                    <h3 className="admin-udfa-block-title">Status</h3>
                    {syncStatus?.backfill?.running && (
                        <p className="admin-status">
                            Backfill in progress: <strong>{syncStatus.backfill.dataset}</strong>
                            {syncStatus.backfill.started_at ? ` (started ${new Date(syncStatus.backfill.started_at).toLocaleTimeString()})` : ''}
                        </p>
                    )}
                    {syncStatus?.scheduler?.jobs?.[0]?.next_run_time && (
                        <p className="admin-status">Next scheduled sync: {new Date(syncStatus.scheduler.jobs[0].next_run_time).toLocaleString()}</p>
                    )}
                    {syncStatus?.recent?.length > 0 ? (
                        <div className="admin-process-results-list">
                            {syncStatus.recent.map(s => (
                                <div key={s.sync_status_id} className="admin-process-result-row">
                                    <span className="admin-process-result-team">
                                        {s.success ? '✓' : '✗'} {s.sync_item}
                                    </span>
                                    <span className="admin-process-result-amount">
                                        {s.timestamp ? new Date(s.timestamp + 'Z').toLocaleString() : ''}
                                    </span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <p className="admin-status">No sync activity recorded yet.</p>
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
