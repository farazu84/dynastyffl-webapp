import { useState, useEffect } from 'react';
import { useAuthFetch } from '../../hooks/useAuthFetch';

const TrophyIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 2C9.239 2 7 4.239 7 7v3H4a1 1 0 0 0-1 1v1c0 2.757 1.998 5.042 4.647 5.791C8.554 19.048 10.132 20 12 20s3.446-.952 4.353-2.209C18.002 17.042 20 14.757 20 12v-1a1 1 0 0 0-1-1h-3V7c0-2.761-2.239-5-5-5zm0 16c-1.105 0-2-.895-2-2h4c0 1.105-.895 2-2 2zm-1 2h2v2h-2v-2z"/>
    </svg>
);

const PlayerResultCard = ({ entry }) => {
    const { player, my_bid, all_bids } = entry;
    const won = my_bid?.status === 'won';
    const variant = my_bid ? (won ? 'won' : 'lost') : 'other';

    return (
        <div className={`result-card result-card--${variant}`}>
            {/* Player identity strip */}
            <div className="result-card-player">
                <div className="result-card-player-left">
                    {player?.position && (
                        <span className={`player-chip-pos player-chip-pos-${player.position.toLowerCase()}`}>
                            {player.position}
                        </span>
                    )}
                    <div className="result-card-player-info">
                        <span className="result-card-player-name">
                            {player ? `${player.first_name} ${player.last_name}` : 'Unknown Player'}
                        </span>
                        <span className="result-card-player-meta">
                            {[player?.nfl_team, player?.college, player?.age ? `Age ${player.age}` : null]
                                .filter(Boolean).join(' · ')}
                        </span>
                    </div>
                </div>
                {my_bid && (
                    <div className={`result-card-outcome result-card-outcome--${won ? 'won' : 'lost'}`}>
                        <span className="result-card-outcome-label">{won ? 'ACQUIRED' : 'OUTBID'}</span>
                        <span className="result-card-outcome-amount">${my_bid.amount}</span>
                    </div>
                )}
            </div>

            {/* Bid breakdown table */}
            {all_bids.length > 0 && (
                <div className="result-bids-table">
                    <div className="result-bids-header">
                        <span>TEAM</span>
                        <span>ORDER</span>
                        <span>WAIVER</span>
                    </div>
                    {all_bids.map((bid, i) => {
                        const isWinner = bid.status === 'won';
                        const isMine = bid.is_mine;
                        return (
                            <div
                                key={i}
                                className={[
                                    'result-bids-row',
                                    isWinner ? 'result-bids-row--winner' : '',
                                    isMine ? 'result-bids-row--mine' : '',
                                ].join(' ').trim()}
                            >
                                <span className="result-bids-rank">#{i + 1}</span>
                                <span className="result-bids-team">
                                    {bid.team_name}
                                    {isMine && <span className="result-bids-you-tag">you</span>}
                                </span>
                                <span className="result-bids-waiver">
                                    {bid.show_waiver && bid.waiver_order != null ? `#${bid.waiver_order}` : '—'}
                                </span>
                                <span className="result-bids-amount">${bid.amount}</span>
                                {isWinner && (
                                    <span className="result-bids-winner-icon"><TrophyIcon /></span>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
};

const BidResults = ({ budget: initialBudget }) => {
    const authFetch = useAuthFetch();
    const [results, setResults] = useState(null);
    const [budget, setBudget] = useState(initialBudget);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchResults = async () => {
            try {
                const res = await authFetch('/udfa/results');
                if (!res.ok) throw new Error('Failed to load bid results');
                const data = await res.json();
                setResults(data.results);
                if (data.budget) setBudget(data.budget);
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };
        fetchResults();
    }, [authFetch]);

    if (isLoading) return <p className="udfa-status">Loading results...</p>;
    if (error) return <p className="udfa-error">{error}</p>;

    const wonEntries = results.filter(r => r.my_bid?.status === 'won');
    const lostEntries = results.filter(r => r.my_bid?.status === 'lost');
    const otherEntries = results.filter(r => !r.my_bid && r.all_bids.some(b => b.status === 'won'));
    const totalSpent = wonEntries.reduce((sum, r) => sum + r.my_bid.amount, 0);

    return (
        <div className="bid-results">
            {/* Summary strip */}
            <div className="bid-results-summary">
                <div className="bid-results-stat">
                    <span className="bid-results-stat-label">Players Won</span>
                    <span className="bid-results-stat-value bid-results-stat-value--won">{wonEntries.length}</span>
                </div>
                <div className="bid-results-stat">
                    <span className="bid-results-stat-label">Total Spent</span>
                    <span className="bid-results-stat-value">${totalSpent}</span>
                </div>
                <div className="bid-results-stat">
                    <span className="bid-results-stat-label">Bids Placed</span>
                    <span className="bid-results-stat-value">{wonEntries.length + lostEntries.length}</span>
                </div>
                {budget && (
                    <div className="bid-results-stat">
                        <span className="bid-results-stat-label">Starting Budget</span>
                        <span className="bid-results-stat-value">${budget.starting_balance}</span>
                    </div>
                )}
            </div>

            {wonEntries.length > 0 && (
                <div className="result-section">
                    <h3 className="result-section-title result-section-title--won">
                        <TrophyIcon /> Acquired ({wonEntries.length})
                    </h3>
                    <div className="result-rows">
                        {wonEntries.map((entry, i) => <PlayerResultCard key={i} entry={entry} />)}
                    </div>
                </div>
            )}

            {lostEntries.length > 0 && (
                <div className="result-section">
                    <h3 className="result-section-title result-section-title--lost">
                        Outbid ({lostEntries.length})
                    </h3>
                    <div className="result-rows">
                        {lostEntries.map((entry, i) => <PlayerResultCard key={i} entry={entry} />)}
                    </div>
                </div>
            )}

            {otherEntries.length > 0 && (
                <div className="result-section">
                    <h3 className="result-section-title result-section-title--other">
                        Other Acquisitions ({otherEntries.length})
                    </h3>
                    <div className="result-rows">
                        {otherEntries.map((entry, i) => <PlayerResultCard key={i} entry={entry} />)}
                    </div>
                </div>
            )}

            {results.length === 0 && (
                <p className="udfa-status">No bids were placed this window.</p>
            )}
        </div>
    );
};

export default BidResults;
