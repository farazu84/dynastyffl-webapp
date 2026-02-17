import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import TradeCard from './TradeCard';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/TradeHistory.css';

const TradeHistory = () => {
    const [trades, setTrades] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchTrades = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);

                const response = await cachedFetch(`${config.API_BASE_URL}/transactions/trades/random`);
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

    const memoizedCards = useMemo(() => {
        return trades.map((txn) => (
            <TradeCard key={txn.transaction_id} transaction={txn} />
        ));
    }, [trades]);

    if (isLoading) {
        return (
            <section className="trade-history-section">
                <div className="trade-history-header">
                    <div className="trade-history-title">
                        <span className="trade-history-icon">&#8644;</span>
                        <h2>Trade History</h2>
                    </div>
                </div>
                <div className="trade-history-loading">Loading trades...</div>
            </section>
        );
    }

    if (fetchError) {
        return (
            <section className="trade-history-section">
                <div className="trade-history-header">
                    <div className="trade-history-title">
                        <span className="trade-history-icon">&#8644;</span>
                        <h2>Trade History</h2>
                    </div>
                </div>
                <div className="trade-history-error">Error loading trades: {fetchError}</div>
            </section>
        );
    }

    return (
        <section className="trade-history-section">
            <div className="trade-history-header">
                <div className="trade-history-title">
                    <span className="trade-history-icon">&#8644;</span>
                    <h2>Trade History</h2>
                </div>
                <Link to="/archive" className="trade-history-view-all">
                    View All
                </Link>
            </div>
            <div className="trade-history-cards">
                {memoizedCards}
            </div>
        </section>
    );
};

export default TradeHistory;
