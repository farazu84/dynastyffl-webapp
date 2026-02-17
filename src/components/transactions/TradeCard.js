import React from 'react';
import { Link } from 'react-router-dom';
import { formatDate, formatPickShort } from '../../utils/formatters';

const TradeCard = ({ transaction }) => {

    // Group assets acquired by each team (roster)
    const getTeamAcquisitions = () => {
        const teamMap = new Map();

        const ensureTeam = (rosterId, teamName) => {
            if (!teamMap.has(rosterId)) {
                teamMap.set(rosterId, {
                    rosterId,
                    teamName: teamName || `Roster ${rosterId}`,
                    assets: [],
                });
            }
            return teamMap.get(rosterId);
        };

        // Initialize teams from roster_moves
        (transaction.roster_moves || []).forEach((rm) => {
            ensureTeam(rm.sleeper_roster_id, rm.team?.team_name);
        });

        // Add players (action === 'add' means this team acquired the player)
        (transaction.player_moves || []).forEach((pm) => {
            if (pm.action === 'add') {
                const team = ensureTeam(pm.sleeper_roster_id, pm.team?.team_name);
                const name = pm.player
                    ? `${pm.player.first_name} ${pm.player.last_name}`
                    : `Player ${pm.player_sleeper_id}`;
                team.assets.push(name);
            }
        });

        // Add draft picks (owner_id = team that receives the pick)
        (transaction.draft_pick_moves || []).forEach((dp) => {
            if (dp.owner_id) {
                const team = ensureTeam(dp.owner_id, dp.team?.team_name);
                team.assets.push(formatPickShort(dp));
            }
        });

        return Array.from(teamMap.values()).filter((t) => t.assets.length > 0);
    };

    const teams = getTeamAcquisitions();

    return (
        <Link to={`/archive/trades/${transaction.transaction_id}`} className="trade-card-link">
            <div className="trade-card">
                <div className="trade-card-header">
                    <span className="trade-card-date">{formatDate(transaction.created_at)}</span>
                    <span className="trade-card-icon">&#8644;</span>
                </div>
                <div className="trade-card-body">
                    {teams.map((team) => (
                        <div className="trade-card-team" key={team.rosterId}>
                            <span className="trade-card-team-name">{team.teamName}</span>
                            <span className="trade-card-assets">
                                {team.assets.join(', ')}
                            </span>
                        </div>
                    ))}
                </div>
            </div>
        </Link>
    );
};

export default React.memo(TradeCard);
