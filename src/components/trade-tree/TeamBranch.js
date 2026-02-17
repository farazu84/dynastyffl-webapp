import React, { useMemo } from 'react';
import BranchCard from './BranchCard';
import PlayerChip from './PlayerChip';
import { formatPickLong } from '../../utils/formatters';

const getPlayerTerminalState = (player, transactions, rosterId, teamName) => {
    const playerTxns = transactions.filter(txn =>
        (txn.player_moves || []).some(m => m.player_sleeper_id === player.sleeper_id)
    );

    if (playerTxns.length === 0) {
        return { type: 'held', label: `Held by ${teamName}`, subtitle: 'No further movement' };
    }

    const lastTxn = playerTxns[playerTxns.length - 1];
    const playerMoves = (lastTxn.player_moves || []).filter(
        m => m.player_sleeper_id === player.sleeper_id
    );

    const wasDropped = playerMoves.some(m => m.action === 'drop' && m.sleeper_roster_id === rosterId);
    const wasAdded = playerMoves.some(m => m.action === 'add' && m.sleeper_roster_id === rosterId);

    if (wasDropped && !wasAdded) {
        if (lastTxn.type === 'trade') {
            const receivingTeam = (lastTxn.roster_moves || [])
                .find(rm => rm.sleeper_roster_id !== rosterId);
            const receiverName = receivingTeam?.team?.team_name || 'another team';
            return { type: 'traded', label: `Traded to ${receiverName}`, subtitle: 'End of branch' };
        }
        return { type: 'released', label: 'Released', subtitle: 'End of branch' };
    }

    return { type: 'held', label: `Held by ${teamName}`, subtitle: 'Still on roster' };
};

const calculateDuration = (startDateStr, endDateStr) => {
    if (!startDateStr) return '';

    const start = new Date(startDateStr);
    const end = endDateStr ? new Date(endDateStr) : new Date();

    // Calculate difference in milliseconds
    const diffTime = Math.abs(end - start);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    // Less than a month
    if (diffDays < 30) {
        return `${diffDays} day${diffDays !== 1 ? 's' : ''}`;
    }

    // Calculate years and months
    let years = end.getFullYear() - start.getFullYear();
    let months = end.getMonth() - start.getMonth();

    if (months < 0) {
        years--;
        months += 12;
    }

    // Formatting
    const parts = [];
    if (years > 0) parts.push(`${years} yr${years !== 1 ? 's' : ''}`);
    if (months > 0) parts.push(`${months} mo${months !== 1 ? 's' : ''}`);

    if (parts.length === 0) return '0 days';
    return parts.join(', ');
};

const TeamBranch = ({ team, pickMetadata = {}, originDate }) => {
    const transactions = team.transactions || [];

    // 1. Aggregate all assets (initial + subsequent) in order
    const orderedAssets = useMemo(() => {
        const assets = [];
        const knownPlayerIds = new Set();
        const knownPickKeys = new Set();

        // Add initial assets (Players first, then Picks)
        (team.acquired_players || []).forEach(p => {
            assets.push({ type: 'player', data: p, acquiredDate: originDate });
            knownPlayerIds.add(p.sleeper_id);
        });
        (team.acquired_picks || []).forEach(p => {
            assets.push({ type: 'pick', data: p, acquiredDate: originDate });
            knownPickKeys.add(`${p.season}-${p.round}-${p.original_owner_id}`);
        });

        // Sort transactions chronologically to find new assets in order
        const sortedTxns = [...transactions].sort((a, b) =>
            new Date(a.created_at) - new Date(b.created_at)
        );

        sortedTxns.forEach(txn => {
            // Check for new players acquired
            (txn.player_moves || []).forEach(move => {
                if (move.action === 'add' && move.sleeper_roster_id === team.sleeper_roster_id) {
                    if (!knownPlayerIds.has(move.player_sleeper_id)) {
                        if (move.player) {
                            assets.push({
                                type: 'player',
                                data: {
                                    sleeper_id: move.player.sleeper_id,
                                    ...move.player
                                },
                                acquiredDate: txn.created_at
                            });
                            knownPlayerIds.add(move.player_sleeper_id);
                        }
                    }
                }
            });

            // Check for new picks acquired
            (txn.draft_pick_moves || []).forEach(move => {
                if (move.owner_id === team.sleeper_roster_id) {
                    const key = `${move.season}-${move.round}-${move.roster_id}`;
                    if (!knownPickKeys.has(key)) {
                        assets.push({
                            type: 'pick',
                            data: {
                                season: move.season,
                                round: move.round,
                                original_owner_id: move.roster_id,
                                pick_no: null,
                                drafted_player: null
                            },
                            acquiredDate: txn.created_at
                        });
                        knownPickKeys.add(key);
                    }
                }
            });
        });

        return assets;
    }, [team.acquired_players, team.acquired_picks, transactions, team.sleeper_roster_id, originDate]);

    return (
        <div className="team-branch">
            <div className="team-branch-header">
                <span className="team-branch-label">BRANCH PATH</span>
                <span className="team-branch-team-name">{team.team_name}</span>
            </div>

            <div className="team-branch-player-columns">
                {orderedAssets.map((asset, i) => {
                    if (asset.type === 'pick') {
                        const pick = asset.data;
                        // Find transactions involving this pick
                        const pickTxns = transactions.filter(txn =>
                            (txn.draft_pick_moves || []).some(m =>
                                m.season === pick.season && m.round === pick.round && m.roster_id === pick.original_owner_id
                            )
                        );

                        // Check metadata first for draft result
                        const metaKey = `${pick.season}:${pick.round}:${pick.original_owner_id}`;
                        const pickMeta = pickMetadata[metaKey];

                        // Determine terminal state for picks
                        // Check if traded away FIRST (takes priority over draft result)
                        let terminal = { type: 'held', label: 'Held', subtitle: 'Not yet used' };
                        let wasTradedAway = false;

                        const lastTxn = pickTxns[pickTxns.length - 1];
                        if (lastTxn) {
                            wasTradedAway = (lastTxn.draft_pick_moves || []).some(m =>
                                m.season === pick.season &&
                                m.round === pick.round &&
                                m.roster_id === pick.original_owner_id &&
                                m.previous_owner_id === team.sleeper_roster_id
                            );
                            if (wasTradedAway) {
                                const receivingTeam = (lastTxn.roster_moves || []).find(rm => rm.sleeper_roster_id !== team.sleeper_roster_id);
                                const receiverName = receivingTeam?.team?.team_name || 'another team';
                                const duration = calculateDuration(asset.acquiredDate, lastTxn.created_at);
                                terminal = {
                                    type: 'traded',
                                    label: `Pick Traded to ${receiverName}`,
                                    subtitle: `Held for ${duration}`
                                };
                            }
                        }

                        if (!wasTradedAway) {
                            if (pickMeta && pickMeta.drafted_player) {
                                terminal = { type: 'drafted', label: 'Drafted', subtitle: 'Pick used' };
                            } else if (pick.drafted_player) {
                                terminal = { type: 'drafted', label: 'Drafted', subtitle: 'Pick used' };
                            }
                        }

                        const draftedPlayer = (pickMeta && pickMeta.drafted_player) || pick.drafted_player;

                        return (
                            <div className="player-branch" key={`pick-${i}`}>
                                <div className="player-branch-header">
                                    <span className="team-branch-pick-label" style={{ display: 'block', marginBottom: '4px' }}>{formatPickLong(pick)}</span>
                                    {draftedPlayer && <PlayerChip player={draftedPlayer} />}
                                </div>

                                {pickTxns.length > 0 ? (
                                    <div className="team-branch-timeline">
                                        {pickTxns.map(txn => (
                                            <BranchCard
                                                key={txn.transaction_id}
                                                transaction={txn}
                                                branchRosterId={team.sleeper_roster_id}
                                            />
                                        ))}
                                    </div>
                                ) : null}

                                <div className={`terminal-badge terminal-badge-${terminal.type}`}>
                                    <span className="terminal-badge-label">{terminal.label}</span>
                                    {terminal.subtitle && (
                                        <span className="terminal-badge-subtitle">{terminal.subtitle}</span>
                                    )}
                                </div>
                            </div>
                        );
                    } else {
                        // Updated Player Logic with Duration
                        const player = asset.data;
                        const playerTxns = transactions.filter(txn =>
                            (txn.player_moves || []).some(m => m.player_sleeper_id === player.sleeper_id)
                        );

                        let terminal = getPlayerTerminalState(player, transactions, team.sleeper_roster_id, team.team_name);

                        // Calculate Duration based on terminal state
                        let durationStr = '';
                        if (terminal.type === 'held') {
                            durationStr = calculateDuration(asset.acquiredDate, null); // null = now
                            terminal = { ...terminal, subtitle: `On roster for ${durationStr}` };
                        } else {
                            // Find the transaction where they left
                            const lastTxn = playerTxns[playerTxns.length - 1];
                            if (lastTxn) {
                                durationStr = calculateDuration(asset.acquiredDate, lastTxn.created_at);
                                terminal = { ...terminal, subtitle: `Rostered for ${durationStr}` };
                            }
                        }

                        return (
                            <div className="player-branch" key={`player-${player.sleeper_id}`}>
                                <div className="player-branch-header">
                                    <PlayerChip player={player} />
                                </div>

                                {playerTxns.length > 0 ? (
                                    <div className="team-branch-timeline">
                                        {playerTxns.map(txn => (
                                            <BranchCard
                                                key={txn.transaction_id}
                                                transaction={txn}
                                                branchRosterId={team.sleeper_roster_id}
                                            />
                                        ))}
                                    </div>
                                ) : null}

                                <div className={`terminal-badge terminal-badge-${terminal.type}`}>
                                    <span className="terminal-badge-label">{terminal.label}</span>
                                    {terminal.subtitle && (
                                        <span className="terminal-badge-subtitle">{terminal.subtitle}</span>
                                    )}
                                </div>
                            </div>
                        );
                    }
                })}
            </div>

            {orderedAssets.length === 0 && (
                <div className="terminal-badge terminal-badge-held">
                    <span className="terminal-badge-label">No ripple effects</span>
                </div>
            )}
        </div>
    );
};

TeamBranch.displayName = 'TeamBranch';

export default React.memo(TeamBranch);
