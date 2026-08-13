import { useState } from 'react';
import { useAuthFetch } from '../../hooks/useAuthFetch';
import { centsOf, formatMoney, isWholeCents } from '../../utils/formatters';

// `fractionHolder` is the player already carrying this team's fractional bid, if any.
const BidModal = ({ player, budget, fractionHolder, onClose, onSuccess }) => {
    const authFetch = useAuthFetch();
    const existingBid = player.my_bid;

    // When editing, the existing bid amount is freed up, so add it back to available
    const available = budget.available + (existingBid?.amount ?? 0);

    // The one fraction this team may spend. 0 when the budget is a whole dollar amount.
    const budgetCents = centsOf(budget.starting_balance);
    // Editing the bid that already holds the fraction must not trip the "already used" rule
    // against itself.
    const fractionUsedElsewhere = fractionHolder && fractionHolder.sleeper_id !== player.sleeper_id;

    const [amount, setAmount] = useState(existingBid?.amount ?? '');
    const [error, setError] = useState(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Mirrors validate_fractional_bid() in app/logic/udfa.py. The server stays authoritative;
    // this exists so a violation is caught before submit and the rule is visible in the UI.
    const validate = (val) => {
        const n = Number(val);
        if (!val && val !== 0) return 'Amount is required.';
        if (Number.isNaN(n)) return 'Amount must be a dollar amount.';
        if (!isWholeCents(n)) return 'Amount cannot be more precise than cents.';
        if (n < 1) return 'Amount must be at least $1.';
        if (n > available) return `Amount exceeds your available budget of $${formatMoney(available)}.`;

        const amountCents = centsOf(n);
        if (amountCents !== 0) {
            // R1 — you must have a fraction to use one.
            if (budgetCents === 0) {
                return 'Your budget has no cents to spend, so bids must be whole dollars.';
            }
            // R2 — if you use the fraction, you use the whole fraction.
            if (amountCents !== budgetCents) {
                return `A fractional bid must use your full $${formatMoney(budgetCents / 100)} `
                    + `— $${formatMoney(amountCents / 100)} is not allowed.`;
            }
            // R3 — the fraction is used once.
            if (fractionUsedElsewhere) {
                return `You have already used your $${formatMoney(budgetCents / 100)} on `
                    + `${fractionHolder.first_name} ${fractionHolder.last_name}. `
                    + 'Retract that bid to move it.';
            }
        }
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
                    Available budget: <strong>${formatMoney(available)}</strong>
                </div>

                {budgetCents > 0 && (
                    <p className="bid-modal-fraction-hint">
                        {fractionUsedElsewhere
                            ? `Your $${formatMoney(budgetCents / 100)} is on `
                              + `${fractionHolder.first_name} ${fractionHolder.last_name} `
                              + '— this bid must be a whole dollar amount.'
                            : `You may use your $${formatMoney(budgetCents / 100)} on one player, `
                              + 'all of it or none of it.'}
                    </p>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="modal-field">
                        <label htmlFor="bid-amount">Bid Amount ($)</label>
                        <input
                            id="bid-amount"
                            type="number"
                            min="1"
                            /* "any" so the browser's own step validation doesn't fight the
                               fractional rules — validate() above is the real gate. */
                            step="any"
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
