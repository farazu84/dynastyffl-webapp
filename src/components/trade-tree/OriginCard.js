import React, { useMemo } from 'react';
import PlayerChip from './PlayerChip';
import { formatDate, formatPickLong } from '../../utils/formatters';

const OriginCard = ({ origin }) => {
    const teamAcquisitions = useMemo(() => {
        const teamMap = new Map();

        const ensureTeam = (rosterId, teamName) => {
            if (!teamMap.has(rosterId)) {
                teamMap.set(rosterId, {
                    teamName: teamName || `Roster ${rosterId}`,
                    players: [],
                    picks: [],
                });
            }
            return teamMap.get(rosterId);
        };

        // Initialize from roster_moves
        (origin.roster_moves || []).forEach(rm => {
            ensureTeam(rm.sleeper_roster_id, rm.team?.team_name);
        });

        // Players acquired (action === 'add')
        (origin.player_moves || []).forEach(pm => {
            if (pm.action === 'add') {
                const team = ensureTeam(pm.sleeper_roster_id, pm.team?.team_name);
                team.players.push(
                    pm.player || { first_name: 'Player', last_name: pm.player_sleeper_id, position: null }
                );
            }
        });

        // Picks acquired (owner_id = receiving team)
        (origin.draft_pick_moves || []).forEach(dp => {
            if (dp.owner_id) {
                const team = ensureTeam(dp.owner_id, dp.team?.team_name);
                team.picks.push(dp);
            }
        });

        return Array.from(teamMap.values()).filter(
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
                                    {formatPickLong(dp)}
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
