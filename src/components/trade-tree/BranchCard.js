import React, { useMemo } from 'react';
import PlayerChip from './PlayerChip';

const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const month = date.toLocaleString('en-US', { month: 'short' }).toUpperCase();
    const day = date.getDate();
    const year = date.getFullYear();
    return `${month} ${day}, ${year}`;
};

const formatPick = (dp) => {
    const roundSuffix = dp.round === 1 ? 'st' : dp.round === 2 ? 'nd' : dp.round === 3 ? 'rd' : 'th';
    return `${dp.season} ${dp.round}${roundSuffix}`;
};

const getAcquisitions = (txn) => {
    const acquisitions = [];
    const teamMap = new Map();

    // 1. Identify all teams involved from roster_moves
    (txn.roster_moves || []).forEach(rm => {
        teamMap.set(rm.sleeper_roster_id, {
            id: rm.sleeper_roster_id,
            name: rm.team?.team_name || `Roster ${rm.sleeper_roster_id}`,
            players: [],
            picks: []
        });
    });

    // 2. Assign players to the team that added them
    (txn.player_moves || []).forEach(pm => {
        if (pm.action === 'add') {
            const team = teamMap.get(pm.sleeper_roster_id);
            if (team && pm.player) {
                team.players.push(pm.player);
            }
        }
    });

    // 3. Assign picks to the new owner
    (txn.draft_pick_moves || []).forEach(dp => {
        const team = teamMap.get(dp.owner_id);
        if (team) {
            team.picks.push(dp);
        }
    });

    // 4. Convert to array and filter out teams with no acquisitions
    return Array.from(teamMap.values()).filter(t => t.players.length > 0 || t.picks.length > 0);
};

const BranchCard = ({ transaction, branchRosterId, trackedPlayerId }) => {
    const acquisitions = useMemo(() => {
        const list = getAcquisitions(transaction);
        // Sort so the branch owner (current team) is last
        return list.sort((a, b) => {
            if (a.id === branchRosterId) return 1;
            if (b.id === branchRosterId) return -1;
            return 0;
        });
    }, [transaction, branchRosterId]);
    const dateStr = formatDate(transaction.created_at);

    // Context for the main label (e.g., "Trade", "Waiver Claim")
    const label = useMemo(() => {
        if (transaction.type === 'trade') return 'Trade';
        if (transaction.type === 'waiver') return 'Waiver Claim';
        if (transaction.type === 'free_agent') return 'Free Agent Move';
        return 'Transaction';
    }, [transaction.type]);

    return (
        <div className="branch-card">
            <div className="branch-card-dot" />
            <div className="branch-card-content">
                <div className="branch-card-top-row">
                    <span className="branch-card-date">{dateStr}</span>
                    <span className="branch-card-label" style={{ marginLeft: '8px', fontSize: '0.9em' }}>
                        {label}
                    </span>
                </div>

                <div className="branch-card-exchange">
                    {acquisitions.map((team) => (
                        <div className="branch-card-exchange-section" key={team.id}>
                            <span className="branch-card-exchange-label" style={{
                                color: team.id === branchRosterId ? '#61dafb' : 'rgba(255, 255, 255, 0.4)',
                                fontSize: '0.75em'
                            }}>
                                {team.name} Acquired:
                            </span>
                            <div className="branch-card-exchange-items">
                                {team.players.map((player, i) => (
                                    <PlayerChip key={`p-${i}`} player={player} />
                                ))}
                                {team.picks.map((pick, i) => (
                                    <span className="branch-card-pick" key={`pik-${i}`}>
                                        {formatPick(pick)}
                                    </span>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

BranchCard.displayName = 'BranchCard';

export default React.memo(BranchCard);
