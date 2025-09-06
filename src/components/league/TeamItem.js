import React from 'react';
import { Link } from 'react-router-dom';

const TeamItem = React.memo(({ team }) => {
    // Get current team record if available
    const currentRecord = team.current_team_record;
    
    return (
        <li className="team" key={team.team_id}>
            <Link to={`/teams/${team.team_id}`} className="team-link">
                <div className="team-info">
                    <p className="team-name">{team.team_name}</p>
                    {currentRecord && (
                        <div className="team-stats">
                            <div className="record">
                                <span className="wins">{currentRecord.wins}</span>
                                <span className="separator">-</span>
                                <span className="losses">{currentRecord.losses}</span>
                            </div>
                            <div className="points">
                                <div className="points-for">
                                    <span className="label">PF:</span>
                                    <span className="value">{currentRecord.points_for?.toFixed(1) || '0.0'}</span>
                                </div>
                                <div className="points-against">
                                    <span className="label">PA:</span>
                                    <span className="value">{currentRecord.points_against?.toFixed(1) || '0.0'}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </Link>
        </li>
    );
});

TeamItem.displayName = 'TeamItem';

export default TeamItem;