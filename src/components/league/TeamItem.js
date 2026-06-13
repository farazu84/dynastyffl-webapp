import React from 'react';
import { Link } from 'react-router-dom';

const RANK_COLORS = ['var(--gold)', 'var(--silver)', 'var(--bronze)'];

const TeamItem = React.memo(({ team, rank, record }) => {
    const currentRecord = record ?? team.current_team_record;
    const rankColor = rank <= 3 ? RANK_COLORS[rank - 1] : 'var(--muted)';

    const ownerName = team?.owners?.map(o => o.user_name).filter(Boolean).join(', ')
        || team?.team_owners?.map(o => o.user?.user_name).filter(Boolean).join(', ')
        || null;

    return (
        <li className="team" key={team.team_id}>
            <Link to={`/teams/${team.team_id}`} className="team-link">
                <div className="team-info">
                    <span className="team-rank" style={{ color: rankColor }}>
                        {String(rank).padStart(2, '0')}
                    </span>
                    <div className="team-left">
                            <p className="team-name">{team.team_name}</p>
                            {ownerName && (
                                <span className="team-owner">{ownerName}</span>
                            )}
                    </div>

                    {currentRecord && (
                        <div className="team-stats">
                            <div className="team-record">
                                <span className="wins">{currentRecord.wins}</span>
                                <span className="separator">·</span>
                                <span className="losses">{currentRecord.losses}</span>
                            </div>
                            <div className="points">
                                <div className="points-for">
                                    <span className="label">PF</span>
                                    <span className="value">{currentRecord.points_for?.toFixed(1) || '0.0'}</span>
                                </div>
                                <span className="points-sep">·</span>
                                <div className="points-against">
                                    <span className="label">PA</span>
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
