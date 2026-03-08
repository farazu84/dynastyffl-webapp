import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

const TeamHeader = ( {team} ) => {
    const { user } = useAuth();

    const isOwner = user && team?.owners?.some(o => o.user_id === user.user_id);

    // Helper function to format names
    const formatName = (user) => {
        const hasFirstLast = user.first_name && user.last_name;
        if (hasFirstLast) {
            return `${user.user_name} (${user.first_name} ${user.last_name})`;
        }
        return user.user_name || 'Unknown User';
    };

    return (
        <div className="title-card">
            <div className="title-card-identity">
                <h2 className="title-card-name">{team.team_name}</h2>
                <p className="title-card-owners">
                    {team?.owners?.map((owner) => formatName(owner)).join(', ')}
                </p>
            </div>

            <div className="title-card-stats">
                {team.championships > 0 ? (
                    <span className="title-stat-chip title-stat-chip--gold">
                        {team.championships}× Champ
                    </span>
                ) : (
                    <span className="title-stat-chip title-stat-chip--muted">
                        No titles yet
                    </span>
                )}
                <span className="title-stat-chip">
                    <span className="title-stat-label">Roster</span>
                    {team.roster_size}
                </span>
                <span className="title-stat-chip">
                    <span className="title-stat-label">Avg Age</span>
                    {team.average_age}
                </span>
                <span className="title-stat-chip">
                    <span className="title-stat-label">Starter Age</span>
                    {team.average_starter_age}
                </span>
            </div>

            {isOwner && (
                <Link className="udfa-bid-link" to={`/udfa/${team.team_id}`}>
                    UDFA Bidding
                </Link>
            )}
        </div>
    )
}

export default TeamHeader