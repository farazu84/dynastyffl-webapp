import React from 'react';

// Standard starting slots before the FLEX kicks in
const POSITION_LIMITS = { QB: 1, RB: 2, WR: 3, TE: 1, K: 1 };
// Positions eligible for the FLEX slot
const FLEX_ELIGIBLE = new Set(['RB', 'WR', 'TE']);

// Sort starters into canonical order so slot numbers are assigned correctly
// before any FLEX overflow is detected.
const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'K'];
const posOrder = (p) => {
    const i = POSITION_ORDER.indexOf(p.position);
    return i === -1 ? 99 : i;
};

export const computeSlots = (players) => {
    const sorted = [...players].sort((a, b) => posOrder(a) - posOrder(b));
    const counts = {};
    const slots = sorted.map((player) => {
        const pos = player.position;
        counts[pos] = (counts[pos] || 0) + 1;
        const limit = POSITION_LIMITS[pos];
        if (limit === undefined) return pos;
        if (counts[pos] <= limit) return limit === 1 ? pos : `${pos}${counts[pos]}`;
        // Beyond the standard limit — goes into the FLEX slot if eligible
        return FLEX_ELIGIBLE.has(pos) ? 'FLEX' : pos;
    });

    // Return slots in the original (unsorted) player order
    const slotMap = new Map(sorted.map((p, i) => [p.player_id, slots[i]]));
    return players.map(p => slotMap.get(p.player_id) ?? p.position);
};

const getAvatarLabel = (player) =>
    player.player_number != null
        ? `${player.player_number}`
        : `${player.first_name?.[0] ?? ''}${player.last_name?.[0] ?? ''}`.toUpperCase();

const formatExp = (years) => {
    if (years === null || years === undefined || years === 0) return 'R';
    return years === 1 ? '1 yr' : `${years} yrs`;
};

const getStatus = (player) => {
    const s = (player.injury_status ?? '').toUpperCase();
    if (!s || s === 'ACTIVE') return { label: 'Healthy', mod: 'healthy' };
    if (s === 'QUESTIONABLE' || s === 'Q') return { label: 'Questionable', mod: 'questionable' };
    if (s === 'IR') return { label: 'IR', mod: 'ir' };
    if (s === 'OUT' || s === 'O') return { label: 'Out', mod: 'out' };
    return { label: s, mod: 'questionable' };
};

const RosterRow = React.memo(({ player, slot }) => {
    const initials = getAvatarLabel(player);
    const status = getStatus(player);

    return (
        <div className="roster-row">
            <div className="roster-slot">
                <span className="roster-slot-badge">{slot}</span>
            </div>

            <div className="roster-player-cell">
                <div className="roster-avatar">{initials}</div>
                <div className="roster-player-info">
                    <span className="roster-player-name">
                        {player.first_name} {player.last_name}
                    </span>
                    {player.college && (
                        <span className="roster-player-sub">{player.college}</span>
                    )}
                </div>
            </div>

            <div className="roster-cell">{player.nfl_team ?? '—'}</div>
            <div className="roster-cell">{player.age ?? '—'}</div>
            <div className="roster-cell">{formatExp(player.years_exp)}</div>
            <div className="roster-col-status">
                <span className={`roster-status roster-status--${status.mod}`}>
                    {status.label}
                </span>
            </div>
        </div>
    );
});

RosterRow.displayName = 'RosterRow';

export default RosterRow;
