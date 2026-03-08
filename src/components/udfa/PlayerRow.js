const EditIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
    </svg>
);

const TrashIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="3 6 5 6 21 6"/>
        <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
        <path d="M10 11v6M14 11v6"/>
        <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/>
    </svg>
);

const PlayerRow = ({ player, onPlaceBid, onEditBid, onRetractBid }) => {
    const { first_name, last_name, position, nfl_team, age, college, my_bid } = player;

    return (
        <div className="player-row-item">
            <div className="player-row-position">
                {position && (
                    <span className={`player-chip-pos player-chip-pos-${position.toLowerCase()}`}>
                        {position}
                    </span>
                )}
            </div>

            <div className="player-info">
                <span className="player-name">{first_name} {last_name}</span>
                <span className="player-meta">Age: {age ?? '—'} · College: {college ?? '—'}</span>
            </div>

            <div className="player-row-nfl-team">
                {nfl_team ?? '—'}
            </div>

            <div className="player-row-bid-status">
                {my_bid ? (
                    <div className="bid-active">
                        <div className="bid-active-info">
                            <span className="bid-active-label">ACTIVE BID</span>
                            <span className="bid-active-amount">${my_bid.amount}</span>
                        </div>
                        <button className="bid-icon-btn" onClick={() => onEditBid(player)} title="Edit bid">
                            <EditIcon />
                        </button>
                        <button className="bid-icon-btn danger" onClick={() => onRetractBid(my_bid.bid_id)} title="Retract bid">
                            <TrashIcon />
                        </button>
                    </div>
                ) : (
                    <button className="place-bid-btn" onClick={() => onPlaceBid(player)}>
                        Place Bid
                    </button>
                )}
            </div>
        </div>
    );
};

export default PlayerRow;
