import { useState, useEffect, useCallback } from 'react';
import { useAuthFetch } from '../../hooks/useAuthFetch';
import BudgetBar from '../../components/udfa/BudgetBar';
import PlayerTable from '../../components/udfa/PlayerTable';
import BidModal from '../../components/udfa/BidModal';
import BidWindowCountdown from '../../components/udfa/BidWindowCountdown';
import BidResults from '../../components/udfa/BidResults';
import '../../styles/UDFA.css';
import '../../styles/TradeTree.css';

const UDFA = () => {
    const authFetch = useAuthFetch();
    const [players, setPlayers] = useState([]);
    const [budget, setBudget] = useState(null);
    const [bidWindow, setBidWindow] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [modalPlayer, setModalPlayer] = useState(null);

    useEffect(() => {
        const fetchUDFAData = async () => {
            try {
                setIsLoading(true);
                setError(null);
                const [playersRes, windowRes] = await Promise.all([
                    authFetch('/udfa/players'),
                    authFetch('/udfa/window'),
                ]);
                if (!playersRes.ok) throw new Error(`Failed to load UDFA data: ${playersRes.status}`);
                const data = await playersRes.json();
                setPlayers(data.players);
                setBudget(data.budget);
                if (windowRes.ok) {
                    const windowData = await windowRes.json();
                    setBidWindow(windowData.window);
                }
            } catch (err) {
                setError(err.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchUDFAData();
    }, [authFetch]);

    const handlePlaceBid = useCallback((player) => {
        setModalPlayer(player);
    }, []);

    const handleEditBid = useCallback((player) => {
        setModalPlayer(player);
    }, []);

    const handleBidSuccess = useCallback((sleeperId, updatedBid, updatedBudget) => {
        setPlayers(prev => prev.map(p =>
            p.sleeper_id === sleeperId ? { ...p, my_bid: updatedBid } : p
        ));
        setBudget(updatedBudget);
    }, []);

    const handleRetractBid = useCallback(async (bidId) => {
        try {
            const res = await authFetch(`/udfa/bids/${bidId}`, { method: 'DELETE' });
            if (!res.ok) return;
            const data = await res.json();
            setPlayers(prev => prev.map(p =>
                p.my_bid?.bid_id === bidId ? { ...p, my_bid: null } : p
            ));
            setBudget(data.budget);
        } catch (err) {
            console.error('Failed to retract bid:', err);
        }
    }, [authFetch]);

    if (isLoading) {
        return <main className="udfa-page"><p className="udfa-status">Loading...</p></main>;
    }

    if (error) {
        return <main className="udfa-page"><p className="udfa-error">{error}</p></main>;
    }

    const isProcessed = bidWindow?.processed;

    return (
        <main className="udfa-page">
            <div className="udfa-header">
                <div className="udfa-header-left">
                    <h2>{isProcessed ? 'UDFA Results' : 'UDFA Player Pool'}</h2>
                    <p>{isProcessed
                        ? 'Bidding is complete. Here\'s how your picks shook out.'
                        : 'Identify and bid on the next breakout rookie stars.'
                    }</p>
                </div>
                <BidWindowCountdown window={bidWindow} />
            </div>

            {isProcessed ? (
                <BidResults budget={budget} />
            ) : (
                <>
                    {budget && <BudgetBar budget={budget} />}
                    <PlayerTable
                        title="Active Bids"
                        players={players.filter(p => p.my_bid)}
                        showFilters={false}
                        onPlaceBid={handlePlaceBid}
                        onEditBid={handleEditBid}
                        onRetractBid={handleRetractBid}
                    />
                    <PlayerTable
                        title="Available Players"
                        players={players.filter(p => !p.my_bid)}
                        onPlaceBid={handlePlaceBid}
                        onEditBid={handleEditBid}
                        onRetractBid={handleRetractBid}
                    />
                    {modalPlayer && budget && (
                        <BidModal
                            player={modalPlayer}
                            budget={budget}
                            onClose={() => setModalPlayer(null)}
                            onSuccess={handleBidSuccess}
                        />
                    )}
                </>
            )}
        </main>
    );
};

export default UDFA;
