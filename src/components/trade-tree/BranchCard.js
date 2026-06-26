import React, { useMemo } from 'react';
import PlayerChip from './PlayerChip';
import { formatDate, formatPickShort, ordinal } from '../../utils/formatters';

const getAcquisitions = (txn) => {
    const teamMap = new Map();

    // 1. Identify all teams involved from roster_moves
    (txn.roster_moves || []).forEach(rm => {
        teamMap.set(rm.sleeper_roster_id, {
            id: rm.sleeper_roster_id,
            name: rm.team?.team_name || `Roster ${rm.sleeper_roster_id}`,
            players: [],
            droppedPlayers: [],
            picks: []
        });
    });

    // 2. Assign players to the team that added/dropped them
    (txn.player_moves || []).forEach(pm => {
        const team = teamMap.get(pm.sleeper_roster_id);
        if (team && pm.player) {
            if (pm.action === 'add') {
                team.players.push(pm.player);
            } else if (pm.action === 'drop') {
                team.droppedPlayers.push(pm.player);
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

    // 4. Convert to array and filter out teams with no activity
    return Array.from(teamMap.values()).filter(t => t.players.length > 0 || t.picks.length > 0 || t.droppedPlayers.length > 0);
};

const BranchCard = ({ transaction, branchRosterId, expansionSelections = {} }) => {
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
        if (transaction.type === 'expansion') return 'Expansion Draft';
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
                            {(team.players.length > 0 || team.picks.length > 0) && (
                                <>
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
                                                {formatPickShort(pick)}
                                            </span>
                                        ))}
                                    </div>
                                </>
                            )}
                            {transaction.type !== 'trade' && team.droppedPlayers.length > 0 && (() => {
                                const selFor = (p) =>
                                    expansionSelections[`${transaction.transaction_id}:${p.sleeper_id}`];
                                const expansionDrops = team.droppedPlayers.filter(p => selFor(p));
                                const releasedDrops = team.droppedPlayers.filter(p => !selFor(p));
                                return (
                                    <>
                                        {expansionDrops.length > 0 && (
                                            <>
                                                <span className="branch-card-exchange-label" style={{
                                                    color: '#b794ff',
                                                    fontSize: '0.75em'
                                                }}>
                                                    Selected in Expansion Draft:
                                                </span>
                                                <div className="branch-card-exchange-items">
                                                    {expansionDrops.map((player, i) => {
                                                        const sel = selFor(player);
                                                        return (
                                                            <span className="branch-card-expansion-pick" key={`x-${i}`}>
                                                                <PlayerChip player={player} />
                                                                <span className="branch-card-expansion-meta" style={{
                                                                    color: '#b794ff',
                                                                    fontSize: '0.7em',
                                                                    marginLeft: '6px'
                                                                }}>
                                                                    {sel.team_name} · {ordinal(sel.round)} Round · {ordinal(sel.pick_no)} Overall
                                                                </span>
                                                            </span>
                                                        );
                                                    })}
                                                </div>
                                            </>
                                        )}
                                        {releasedDrops.length > 0 && (
                                            <>
                                                <span className="branch-card-exchange-label" style={{
                                                    color: '#ff6b6b',
                                                    fontSize: '0.75em'
                                                }}>
                                                    Released:
                                                </span>
                                                <div className="branch-card-exchange-items">
                                                    {releasedDrops.map((player, i) => (
                                                        <PlayerChip key={`d-${i}`} player={player} />
                                                    ))}
                                                </div>
                                            </>
                                        )}
                                    </>
                                );
                            })()}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

BranchCard.displayName = 'BranchCard';

export default React.memo(BranchCard);
