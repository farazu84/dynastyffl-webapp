import { useState, useEffect } from 'react';

const getTimeLeft = (closesAt) => {
    const diff = new Date(closesAt) - Date.now();
    if (diff <= 0) return null;
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    return { d, h, m, s };
};

const BidWindowCountdown = ({ window: bidWindow }) => {
    const [timeLeft, setTimeLeft] = useState(
        bidWindow?.closes_at ? getTimeLeft(bidWindow.closes_at) : null
    );

    useEffect(() => {
        if (!bidWindow?.closes_at || !bidWindow?.is_open) return;
        const id = setInterval(() => {
            const t = getTimeLeft(bidWindow.closes_at);
            setTimeLeft(t);
            if (!t) clearInterval(id);
        }, 1000);
        return () => clearInterval(id);
    }, [bidWindow]);

    if (!bidWindow) return null;

    let label, value, valueClass;

    if (bidWindow.processed) {
        label = 'BID WINDOW';
        value = 'Processed';
        valueClass = 'bid-window-closed';
    } else if (!bidWindow.is_open) {
        if (new Date(bidWindow.opens_at) > Date.now()) {
            label = 'WINDOW OPENS';
            const t = getTimeLeft(bidWindow.opens_at);
            value = t ? `${t.d}d ${t.h}h ${t.m}m` : 'Soon';
        } else {
            label = 'BID WINDOW';
            value = 'Closed';
            valueClass = 'bid-window-closed';
        }
    } else if (timeLeft) {
        label = 'TIME REMAINING';
        const parts = [];
        if (timeLeft.d > 0) parts.push(`${timeLeft.d}d`);
        parts.push(`${String(timeLeft.h).padStart(2, '0')}h`);
        parts.push(`${String(timeLeft.m).padStart(2, '0')}m`);
        parts.push(`${String(timeLeft.s).padStart(2, '0')}s`);
        value = parts.join(' ');
        valueClass = 'bid-window-open';
    } else {
        label = 'BID WINDOW';
        value = 'Closed';
        valueClass = 'bid-window-closed';
    }

    return (
        <div className="bid-window-countdown">
            <span className="bid-window-label">{label}</span>
            <span className={`bid-window-value ${valueClass || ''}`}>{value}</span>
        </div>
    );
};

export default BidWindowCountdown;
