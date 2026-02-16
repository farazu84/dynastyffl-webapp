import React, { useMemo } from 'react';
import BranchCard from './BranchCard';
import PlayerChip from './PlayerChip';

const formatPick = (pick) => {
    const roundSuffix = pick.round === 1 ? 'st' : pick.round === 2 ? 'nd' : pick.round === 3 ? 'rd' : 'th';
    let label = `${pick.season} ${pick.round}${roundSuffix} Round Pick`;
    if (pick.pick_no) {
        label += ` (#${pick.pick_no})`;
    }
    return label;
};

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
            return { type: 'ended', label: `Traded to ${receiverName}`, subtitle: 'End of branch' };
        }
        return { type: 'ended', label: 'Released', subtitle: 'End of branch' };
    }

    return { type: 'held', label: `Held by ${teamName}`, subtitle: 'Still on roster' };
};

const TeamBranch = ({ team }) => {
    const transactions = team.transactions || [];
    const acquiredPlayers = team.acquired_players || [];
    const acquiredPicks = team.acquired_picks || [];

    // Build per-player sub-branches: filter transactions to those involving each player
    const playerBranches = useMemo(() => {
        return acquiredPlayers.map(player => {
            const playerTxns = transactions.filter(txn =>
                (txn.player_moves || []).some(m => m.player_sleeper_id === player.sleeper_id)
            );
            const terminal = getPlayerTerminalState(player, transactions, team.sleeper_roster_id, team.team_name);
            return { player, transactions: playerTxns, terminal };
        });
    }, [acquiredPlayers, transactions, team.sleeper_roster_id, team.team_name]);

    return (
        <div className="team-branch">
            <div className="team-branch-header">
                <span className="team-branch-label">BRANCH PATH</span>
                <span className="team-branch-team-name">{team.team_name}</span>
            </div>

            {acquiredPicks.length > 0 && (
                <div className="team-branch-acquired">
                    <span className="team-branch-acquired-label">Acquired Picks</span>
                    <div className="team-branch-picks">
                        {acquiredPicks.map((pick, i) => (
                            <div className="team-branch-pick" key={i}>
                                <span className="team-branch-pick-label">{formatPick(pick)}</span>
                                {pick.drafted_player ? (
                                    <span className="team-branch-pick-result">
                                        Drafted: <PlayerChip player={pick.drafted_player} />
                                    </span>
                                ) : (
                                    <span className="team-branch-pick-pending">Pick not yet used</span>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {playerBranches.length > 0 && (
                <div className="team-branch-player-columns">
                    {playerBranches.map(({ player, transactions: playerTxns, terminal }) => (
                        <div className="player-branch" key={player.sleeper_id}>
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
                                            trackedPlayerId={player.sleeper_id}
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
                    ))}
                </div>
            )}

            {playerBranches.length === 0 && acquiredPicks.length === 0 && (
                <div className="terminal-badge terminal-badge-held">
                    <span className="terminal-badge-label">No ripple effects</span>
                </div>
            )}
        </div>
    );
};

TeamBranch.displayName = 'TeamBranch';

export default React.memo(TeamBranch);
