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
    return `${dp.season} ${dp.round}${roundSuffix} Round Pick`;
};

const OriginCard = ({ origin }) => {
    const teamAcquisitions = useMemo(() => {
        const teamMap = {};

        // Initialize from roster_moves
        (origin.roster_moves || []).forEach(rm => {
            const rosterId = rm.sleeper_roster_id;
            if (!teamMap[rosterId]) {
                teamMap[rosterId] = {
                    teamName: rm.team?.team_name || `Roster ${rosterId}`,
                    players: [],
                    picks: [],
                };
            }
        });

        // Players acquired (action === 'add')
        (origin.player_moves || []).forEach(pm => {
            if (pm.action === 'add') {
                const rosterId = pm.sleeper_roster_id;
                if (!teamMap[rosterId]) {
                    teamMap[rosterId] = {
                        teamName: pm.team?.team_name || `Roster ${rosterId}`,
                        players: [],
                        picks: [],
                    };
                }
                teamMap[rosterId].players.push(
                    pm.player || { first_name: 'Player', last_name: pm.player_sleeper_id, position: null }
                );
            }
        });

        // Picks acquired (owner_id = receiving team)
        (origin.draft_pick_moves || []).forEach(dp => {
            const rosterId = dp.owner_id;
            if (rosterId && teamMap[rosterId]) {
                teamMap[rosterId].picks.push(dp);
            }
        });

        return Object.values(teamMap).filter(
            t => t.players.length > 0 || t.picks.length > 0
        );
    }, [origin]);

    return (
        <div className="origin-card">
            <div className="origin-card-header">
                <span className="origin-card-badge">ORIGIN TRANSACTION</span>
                <span className="origin-card-date">{formatDate(origin.created_at)}</span>
            </div>
            <div className="origin-card-teams">
                {teamAcquisitions.map((team, idx) => (
                    <div className="origin-card-team" key={idx}>
                        <span className="origin-card-team-label">ACQUIRED BY</span>
                        <span className="origin-card-team-name">{team.teamName}</span>
                        <div className="origin-card-assets">
                            {team.players.map((p, i) => (
                                <PlayerChip key={i} player={p} />
                            ))}
                            {team.picks.map((dp, i) => (
                                <span className="origin-card-pick" key={`pick-${i}`}>
                                    {formatPick(dp)}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

OriginCard.displayName = 'OriginCard';

export default React.memo(OriginCard);
