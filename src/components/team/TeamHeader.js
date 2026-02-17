const TeamHeader = ( {team} ) => {
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
            <h2>{team.team_name}</h2>
            <h3>Team Owner(s): {team?.owners?.map((owner) => formatName(owner)).join(', ')}</h3>
            {team.championships &&
                <>
                    <p>{team.championships}x Champion</p>
                </>
            }
            <p>Roster Size: {team.roster_size}</p>
            <p>Average Age: {team.average_age}</p>
            <p>Average Starter Age: {team.average_starter_age}</p>

        </div>
    )
}

export default TeamHeader