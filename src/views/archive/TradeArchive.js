import React, { useState, useEffect, useMemo } from 'react';
import TradeCard from '../../components/transactions/TradeCard';
import Pagination from '../../components/shared/Pagination';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/TradeArchive.css';

const PER_PAGE = 10;

const TradeArchive = () => {
    const [trades, setTrades] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    const [year, setYear] = useState('all');
    const [team, setTeam] = useState('all');
    const [sort, setSort] = useState('newest');
    const [page, setPage] = useState(1);

    useEffect(() => {
        const fetchTrades = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);

                const response = await cachedFetch(`${config.API_BASE_URL}/transactions?type=trade`);
                if (!response.ok) throw new Error(`API error: ${response.status}`);

                const data = await response.json();
                setTrades(data.transactions || []);
            } catch (error) {
                setFetchError(error.message);
                setTrades([]);
            } finally {
                setIsLoading(false);
            }
        };

        fetchTrades();
    }, []);

    // Distinct filter options derived from the fetched data.
    const years = useMemo(() => {
        const set = new Set(trades.map((t) => t.year).filter(Boolean));
        return Array.from(set).sort((a, b) => b - a);
    }, [trades]);

    const teams = useMemo(() => {
        const map = new Map();
        trades.forEach((t) => {
            (t.roster_moves || []).forEach((rm) => {
                const name = rm.team?.team_name;
                if (name && !map.has(name)) map.set(name, name);
            });
        });
        return Array.from(map.values()).sort((a, b) => a.localeCompare(b));
    }, [trades]);

    const filtered = useMemo(() => {
        let result = trades.filter((t) => {
            if (year !== 'all' && t.year !== parseInt(year, 10)) return false;
            if (team !== 'all' && !(t.roster_moves || []).some((rm) => rm.team?.team_name === team)) return false;
            return true;
        });

        result = [...result].sort((a, b) => {
            const diff = new Date(a.created_at) - new Date(b.created_at);
            return sort === 'oldest' ? diff : -diff;
        });

        return result;
    }, [trades, year, team, sort]);

    const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
    const currentPage = Math.min(page, totalPages);
    const pageItems = useMemo(() => {
        const start = (currentPage - 1) * PER_PAGE;
        return filtered.slice(start, start + PER_PAGE);
    }, [filtered, currentPage]);

    const hasFilters = year !== 'all' || team !== 'all';

    const handleYear = (e) => { setYear(e.target.value); setPage(1); };
    const handleTeam = (e) => { setTeam(e.target.value); setPage(1); };
    const handleSort = (e) => { setSort(e.target.value); setPage(1); };
    const clearFilters = () => { setYear('all'); setTeam('all'); setSort('newest'); setPage(1); };

    const renderBody = () => {
        if (isLoading) {
            return <div className="trade-archive-status">Loading trades...</div>;
        }
        if (fetchError) {
            return <div className="trade-archive-status trade-archive-error">Error loading trades: {fetchError}</div>;
        }
        if (filtered.length === 0) {
            return (
                <div className="trade-archive-empty">
                    <span className="trade-archive-empty-icon">&#8644;</span>
                    <p>No trades match your filters</p>
                    {hasFilters && (
                        <button className="trade-archive-clear" onClick={clearFilters}>
                            Clear Filters
                        </button>
                    )}
                </div>
            );
        }
        return (
            <>
                <div className="trade-history-cards">
                    {pageItems.map((txn) => (
                        <TradeCard key={txn.transaction_id} transaction={txn} />
                    ))}
                </div>
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={setPage}
                />
            </>
        );
    };

    return (
        <div className="trade-archive-page">
            <div className="trade-archive-header">
                <div className="trade-archive-title">
                    <span className="trade-archive-icon">&#8644;</span>
                    <h1>Trade History</h1>
                </div>
                {!isLoading && !fetchError && (
                    <span className="trade-archive-count">
                        {filtered.length}<span className="trade-archive-count-sep"> / {trades.length}</span> trades
                    </span>
                )}
            </div>

            <div className="trade-archive-filters">
                <select
                    className={`trade-archive-select${year !== 'all' ? ' is-active' : ''}`}
                    value={year}
                    onChange={handleYear}
                >
                    <option value="all">All Years</option>
                    {years.map((y) => (
                        <option key={y} value={y}>{y}</option>
                    ))}
                </select>

                <select
                    className={`trade-archive-select${team !== 'all' ? ' is-active' : ''}`}
                    value={team}
                    onChange={handleTeam}
                >
                    <option value="all">All Teams</option>
                    {teams.map((t) => (
                        <option key={t} value={t}>{t}</option>
                    ))}
                </select>

                <select className="trade-archive-select" value={sort} onChange={handleSort}>
                    <option value="newest">Newest First</option>
                    <option value="oldest">Oldest First</option>
                </select>

                {hasFilters && (
                    <button className="trade-archive-clear" onClick={clearFilters}>
                        &#10005; Clear
                    </button>
                )}
            </div>

            <div className="trade-archive-content">
                {renderBody()}
            </div>
        </div>
    );
};

export default TradeArchive;
