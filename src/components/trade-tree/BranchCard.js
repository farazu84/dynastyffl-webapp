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

const describeTransaction = (txn, branchRosterId, trackedPlayerId) => {
    const type = txn.type;
    const playerMoves = txn.player_moves || [];
    const draftPickMoves = txn.draft_pick_moves || [];

    // Find the tracked player's move in this transaction
    const trackedMove = playerMoves.find(m => m.player_sleeper_id === trackedPlayerId);
    const trackedPlayerName = trackedMove?.player
        ? `${trackedMove.player.first_name} ${trackedMove.player.last_name}`
        : '';

    if (type === 'trade') {
        const otherTeams = (txn.roster_moves || [])
            .filter(rm => rm.sleeper_roster_id !== branchRosterId)
            .map(rm => rm.team?.team_name || `Roster ${rm.sleeper_roster_id}`);
        const otherTeamName = otherTeams.join(' & ') || 'another team';

        // What this team gave up
        const teamDrops = playerMoves.filter(
            m => m.action === 'drop' && m.sleeper_roster_id === branchRosterId
        );
        // What this team received
        const teamAdds = playerMoves.filter(
            m => m.action === 'add' && m.sleeper_roster_id === branchRosterId
        );
        // Picks this team received
        const picksReceived = draftPickMoves.filter(dp => dp.owner_id === branchRosterId);
        // Picks this team gave up
        const picksGiven = draftPickMoves.filter(dp => dp.previous_owner_id === branchRosterId);

        const wasTrackedDropped = trackedMove?.action === 'drop' && trackedMove?.sleeper_roster_id === branchRosterId;

        if (wasTrackedDropped) {
            return {
                label: `Traded ${trackedPlayerName} to ${otherTeamName}`,
                received: teamAdds,
                receivedPicks: picksReceived,
                given: [],
                givenPicks: [],
                icon: '↗',
            };
        }

        return {
            label: `Trade with ${otherTeamName}`,
            received: teamAdds,
            receivedPicks: picksReceived,
            given: teamDrops,
            givenPicks: picksGiven,
            icon: '⇄',
        };
    }

    if (type === 'free_agent') {
        const drops = playerMoves.filter(m => m.action === 'drop');
        const adds = playerMoves.filter(m => m.action === 'add');

        if (trackedMove?.action === 'drop') {
            const teamName = trackedMove.team?.team_name || '';
            return {
                label: `Dropped ${trackedPlayerName}`,
                subtitle: teamName ? `Released by ${teamName}` : null,
                icon: '↓',
                received: [],
                receivedPicks: [],
                given: [],
                givenPicks: [],
            };
        }
        if (trackedMove?.action === 'add') {
            const teamName = trackedMove.team?.team_name || '';
            return {
                label: `Picked up by ${teamName}`,
                subtitle: 'Free Agent Claim',
                icon: '↑',
                received: [],
                receivedPicks: [],
                given: [],
                givenPicks: [],
            };
        }
        // Fallback
        return {
            label: 'Roster move',
            subtitle: 'Free Agent',
            icon: '↕',
            received: adds,
            receivedPicks: [],
            given: drops,
            givenPicks: [],
        };
    }

    if (type === 'waiver') {
        const teamName = trackedMove?.team?.team_name || '';
        return {
            label: `Picked up by ${teamName}`,
            subtitle: 'Waiver Claim',
            icon: '✋',
            received: [],
            receivedPicks: [],
            given: [],
            givenPicks: [],
        };
    }

    return { label: txn.type, icon: '•', received: [], receivedPicks: [], given: [], givenPicks: [] };
};

const BranchCard = ({ transaction, branchRosterId, trackedPlayerId }) => {
    const description = useMemo(
        () => describeTransaction(transaction, branchRosterId, trackedPlayerId),
        [transaction, branchRosterId, trackedPlayerId]
    );

    const hasExchangeDetails = (description.received?.length > 0 || description.receivedPicks?.length > 0);

    return (
        <div className="branch-card">
            <div className="branch-card-dot" />
            <div className="branch-card-content">
                <div className="branch-card-top-row">
                    <span className="branch-card-date">
                        {formatDate(transaction.created_at)}
                    </span>
                    <span className="branch-card-icon">{description.icon}</span>
                </div>
                <div className="branch-card-description">
                    <span className="branch-card-label">{description.label}</span>
                    {description.subtitle && (
                        <span className="branch-card-subtitle">{description.subtitle}</span>
                    )}
                </div>

                {hasExchangeDetails && (
                    <div className="branch-card-exchange">
                        {description.received.length > 0 && (
                            <div className="branch-card-exchange-section">
                                <span className="branch-card-exchange-label">Received:</span>
                                <div className="branch-card-exchange-items">
                                    {description.received.map((move, i) =>
                                        move.player ? (
                                            <PlayerChip key={i} player={move.player} />
                                        ) : null
                                    )}
                                </div>
                            </div>
                        )}
                        {description.receivedPicks.length > 0 && (
                            <div className="branch-card-exchange-section">
                                {description.received.length === 0 && (
                                    <span className="branch-card-exchange-label">Received:</span>
                                )}
                                <div className="branch-card-exchange-items">
                                    {description.receivedPicks.map((dp, i) => (
                                        <span className="branch-card-pick" key={i}>
                                            {formatPick(dp)}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

BranchCard.displayName = 'BranchCard';

export default React.memo(BranchCard);
