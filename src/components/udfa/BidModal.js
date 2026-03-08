import { useState } from 'react';
import { useAuthFetch } from '../../hooks/useAuthFetch';

const BidModal = ({ player, budget, onClose, onSuccess }) => {
    const authFetch = useAuthFetch();
    const existingBid = player.my_bid;

    // When editing, the existing bid amount is freed up, so add it back to available
    const available = budget.available + (existingBid?.amount ?? 0);

    const [amount, setAmount] = useState(existingBid?.amount ?? '');
    const [error, setError] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const validate = (val) => {
        const n = Number(val);
        if (!val && val !== 0) return 'Amount is required.';
        if (!Number.isInteger(n)) return 'Amount must be a whole dollar amount.';
        if (n < 1) return 'Amount must be at least $1.';
        if (n > available) return `Amount exceeds your available budget of $${available}.`;
        return null;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const validationError = validate(amount);
        if (validationError) { setError(validationError); return; }

        setIsSubmitting(true);
        setError(null);

        try {
            const res = await authFetch('/udfa/bids', {
                method: 'POST',
                body: JSON.stringify({
                    player_sleeper_id: player.sleeper_id,
                    amount: Number(amount),
                }),
            });
            const data = await res.json();
            if (!res.ok) { setError(data.error || 'Failed to place bid.'); return; }
            onSuccess(player.sleeper_id, data.bid, data.budget);
            onClose();
        } catch (err) {
            setError('Something went wrong. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>✕</button>

                <h2>{existingBid ? 'Edit Bid' : 'Place Bid'}</h2>

                <div className="bid-modal-player-info">
                    <div className="bid-modal-player-name-row">
                        <span className="bid-modal-player-name">
                            {player.first_name} {player.last_name}
                        </span>
                        {player.position && (
                            <span className={`player-chip-pos player-chip-pos-${player.position.toLowerCase()}`}>
                                {player.position}
                            </span>
                        )}
                    </div>
                    <div className="bid-modal-player-meta">
                        {player.nfl_team && <span>{player.nfl_team}</span>}
                        {player.age && <span>Age: {player.age}</span>}
                        {player.college && <span>{player.college}</span>}
                    </div>
                </div>

                <div className="bid-modal-budget">
                    Available budget: <strong>${available}</strong>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="modal-field">
                        <label htmlFor="bid-amount">Bid Amount ($)</label>
                        <input
                            id="bid-amount"
                            type="number"
                            min="1"
                            step="1"
                            value={amount}
                            onChange={e => { setAmount(e.target.value); setError(null); }}
                            placeholder="Enter amount"
                            autoFocus
                        />
                    </div>
                    {error && <p className="modal-error">{error}</p>}
                    <button className="modal-submit" type="submit" disabled={isSubmitting}>
                        {isSubmitting ? 'Submitting...' : existingBid ? 'Update Bid' : 'Place Bid'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default BidModal;
