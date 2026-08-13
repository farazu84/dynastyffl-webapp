/**
 * Shared formatting utilities for dates, draft picks, and money.
 */

const ordinalSuffix = (n) =>
    n === 1 ? 'st' : n === 2 ? 'nd' : n === 3 ? 'rd' : 'th';

// UDFA budgets and bids can carry cents ($110.50), so amounts arrive as JSON floats and summing
// them client-side produces artifacts like 110.50000000000001. Everything money-shaped goes
// through these two helpers rather than being interpolated raw.

// The cents portion of an amount as a whole number of cents: 110.5 -> 50, 100 -> 0.
// Integer math on purpose — `110.5 % 1 === 0.5` happens to hold, but float remainders are not
// reliable across values like .05, and the fractional bid rules compare these for equality.
export const centsOf = (n) => Math.round(Number(n) * 100) % 100;

// True when an amount is no more precise than cents. Needs the epsilon: 10.05 * 100 is
// 1004.9999999999999, so an exact `Math.round(n * 100) === n * 100` rejects legal $0.05 amounts.
export const isWholeCents = (n) => Math.abs(Math.round(Number(n) * 100) - Number(n) * 100) < 1e-6;

// "110.50" for fractional amounts, "100" for whole ones. Callers supply the $.
export const formatMoney = (n) => {
    const value = Number(n) || 0;
    return centsOf(value) === 0 ? String(Math.round(value)) : value.toFixed(2);
};

// "1st", "2nd", "3rd", "11th", "21st", "23rd" — correct English ordinal (handles the teens)
export const ordinal = (n) => {
    const v = n % 100;
    const suffix = v >= 11 && v <= 13 ? 'th' : (['th', 'st', 'nd', 'rd'][n % 10] || 'th');
    return `${n}${suffix}`;
};

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
