import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const TeamHeader = ({ team, starterCount, benchCount, taxiCount }) => {
    const { user } = useAuth();

    const isOwner = user && team?.owners?.some(o => o.user_id === user.user_id);

    const record = team?.current_team_record;
    const wins = record?.wins ?? 0;
    const losses = record?.losses ?? 0;
    const gamesPlayed = wins + losses;

    const pointsFor = record?.points_for ?? 0;
    const pointsAgainst = record?.points_against ?? 0;
    const avgPerWk = gamesPlayed > 0 ? (pointsFor / gamesPlayed).toFixed(1) : '—';
    const ptDiff = gamesPlayed > 0
        ? `${pointsFor - pointsAgainst >= 0 ? '+' : ''}${(pointsFor - pointsAgainst).toFixed(1)} diff`
        : '—';

    const ownerNames = (team?.owners?.length
        ? team.owners.map(o => o.user_name).filter(Boolean)
        : team?.team_owners?.map(o => o.user?.user_name).filter(Boolean) ?? []
    );
    const ownerDisplay = ownerNames.length ? ownerNames.join(', ') : '—';

    return (
        <div className="th-bar">
            {/* Identity */}
            <div className="th-identity">
                <span className="th-team-name">{team?.team_name ?? '—'}</span>
                <span className="th-owner-line">
                    Owner <strong>{ownerDisplay}</strong>
                </span>
            </div>

            {/* Stats */}
            <div className="th-stats">
                <div className="th-stat">
                    <span className="th-stat-label">Record</span>
                    <span className="th-stat-value">
                        {wins} <span style={{ color: 'var(--stroke-2)', fontSize: '1rem' }}>·</span> {losses}
                    </span>
                    <span className="th-stat-sub">
                        {gamesPlayed > 0 ? `${wins > losses ? 'W' : losses > wins ? 'L' : 'T'}${Math.abs(wins - losses)}` : 'No games'}
                    </span>
                </div>

                <div className="th-stat">
                    <span className="th-stat-label">Points For</span>
                    <span className="th-stat-value">{pointsFor > 0 ? pointsFor.toFixed(1) : '—'}</span>
                    <span className="th-stat-sub">{avgPerWk !== '—' ? `${avgPerWk} avg / wk` : '—'}</span>
                </div>

                <div className="th-stat">
                    <span className="th-stat-label">Points Against</span>
                    <span className="th-stat-value">{pointsAgainst > 0 ? pointsAgainst.toFixed(1) : '—'}</span>
                    <span className="th-stat-sub">{ptDiff}</span>
                </div>

                <div className="th-stat">
                    <span className="th-stat-label">Roster</span>
                    <span className="th-stat-value">{team?.roster_size ?? '—'}</span>
                    <span className="th-stat-sub">
                        {starterCount} / {benchCount} / {taxiCount}
                    </span>
                </div>

                <div className="th-stat">
                    <span className="th-stat-label">Starter Age</span>
                    <span className="th-stat-value th-stat-value--gold">
                        {team?.average_starter_age?.toFixed(2) ?? '—'}
                    </span>
                    <span className="th-stat-sub">
                        avg {team?.average_age?.toFixed(2) ?? '—'}
                    </span>
                </div>
            </div>

            {/* Actions */}
            {isOwner && (
                <div className="th-actions">
                    <Link className="th-action-btn" to={`/udfa/${team.team_id}`}>
                        UDFA Bidding
                    </Link>
                </div>
            )}
        </div>
    );
};

export default TeamHeader;
