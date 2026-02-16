import React from 'react';
import { Link } from 'react-router-dom';

const TradeCard = ({ transaction }) => {
    const formatDate = (dateStr) => {
        if (!dateStr) return '';
        const date = new Date(dateStr);
        const month = date.toLocaleString('en-US', { month: 'short' }).toUpperCase();
        const day = date.getDate();
        const year = date.getFullYear();
        return `${month} ${day}, ${year}`;
    };

    // Group assets acquired by each team (roster)
    const getTeamAcquisitions = () => {
        const teamMap = {};

        // Initialize teams from roster_moves
        (transaction.roster_moves || []).forEach((rm) => {
            const rosterId = rm.sleeper_roster_id;
            if (!teamMap[rosterId]) {
                teamMap[rosterId] = {
                    teamName: rm.team?.team_name || `Roster ${rosterId}`,
                    assets: [],
                };
            }
        });

        // Add players (action === 'add' means this team acquired the player)
        (transaction.player_moves || []).forEach((pm) => {
            if (pm.action === 'add') {
                const rosterId = pm.sleeper_roster_id;
                if (!teamMap[rosterId]) {
                    teamMap[rosterId] = {
                        teamName: pm.team?.team_name || `Roster ${rosterId}`,
                        assets: [],
                    };
                }
                const name = pm.player
                    ? `${pm.player.first_name} ${pm.player.last_name}`
                    : `Player ${pm.player_sleeper_id}`;
                teamMap[rosterId].assets.push(name);
            }
        });

        // Add draft picks (owner_id = team that receives the pick)
        (transaction.draft_pick_moves || []).forEach((dp) => {
            const rosterId = dp.owner_id;
            if (rosterId && teamMap[rosterId]) {
                const roundSuffix = dp.round === 1 ? 'st' : dp.round === 2 ? 'nd' : dp.round === 3 ? 'rd' : 'th';
                teamMap[rosterId].assets.push(`${dp.season} ${dp.round}${roundSuffix}`);
            }
        });

        return Object.values(teamMap).filter((t) => t.assets.length > 0);
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
                    {teams.map((team, idx) => (
                        <div className="trade-card-team" key={idx}>
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
