/**
 * Shared formatting utilities for dates and draft picks.
 */

const ordinalSuffix = (n) =>
    n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th';

// "MAR 5, 2024" — used in trade cards and trade tree timeline
export const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const month = date.toLocaleString('en-US', { month: 'short' }).toUpperCase();
    const day = date.getDate();
    const year = date.getFullYear();
    return `${month} ${day}, ${year}`;
};

// "2025 1st" — compact pick label for trade cards
export const formatPickShort = (dp) => {
    return `${dp.season} ${dp.round}${ordinalSuffix(dp.round)}`;
};

// "2025 1st Round Pick" or "2025 1st Round Pick (#5)" — full label for trade trees
export const formatPickLong = (dp) => {
    let label = `${dp.season} ${dp.round}${ordinalSuffix(dp.round)} Round Pick`;
    if (dp.pick_no) {
        label += ` (#${dp.pick_no})`;
    }
    return label;
};
