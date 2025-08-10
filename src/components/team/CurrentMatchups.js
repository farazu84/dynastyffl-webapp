const CurrentMatchups = ( {matchups} ) => {
    // Split matchups: first one is "next", rest are "upcoming"
    const nextMatchup = matchups.length > 0 ? matchups[0] : null;
    const upcomingMatchups = matchups.length > 1 ? matchups.slice(1) : [];

    const getOpponentTeam = (matchup) => {
        // Return the opponent team data from the matchup
        return matchup.opponent_team;
    };

    const getStartingPlayer = (team, position) => {
        if (!team.players) return null;
        return team.players.find(player => 
            player.position === position && player.starter === true
        );
    };

    const renderMatchupDetails = (matchup, isNext = false) => {
        const opponent = getOpponentTeam(matchup);
        if (!opponent) return <p>Opponent data not available</p>;

        const opponentOwner = opponent.team_owners && opponent.team_owners.length > 0 
            ? opponent.team_owners[0].user.user_name 
            : 'Unknown Owner';

        const startingQB = getStartingPlayer(opponent, 'QB');
        const startingRB = getStartingPlayer(opponent, 'RB');
        const startingWR = getStartingPlayer(opponent, 'WR');
        const startingTE = getStartingPlayer(opponent, 'TE');

        return (
            <div key={matchup.matchup_id} className="title-card">
                <h3>Week {matchup.week} vs {opponent.team_name}</h3>
                <div className="player-row">
                    <div className="player-col">
                        <p><strong>Owner:</strong> {opponentOwner}</p>
                        <p><strong>Average Starter Age:</strong> {opponent.average_starter_age || 'N/A'}</p>
                    </div>
                </div>
                
                <div className="player-col" style={{ marginTop: '10px', width: '100%' }}>
                    <h3>Key Starters:</h3>
                    <div className="player-row" style={{ flexWrap: 'wrap', gap: '15px' }}>
                        {startingQB && (
                            <div className="player-col">
                                <p className="position"><strong>QB</strong></p>
                                <p>{startingQB.first_name} {startingQB.last_name}</p>
                                <p>({startingQB.nfl_team})</p>
                            </div>
                        )}
                        {startingRB && (
                            <div className="player-col">
                                <p className="position"><strong>RB</strong></p>
                                <p>{startingRB.first_name} {startingRB.last_name}</p>
                                <p>({startingRB.nfl_team})</p>
                            </div>
                        )}
                        {startingWR && (
                            <div className="player-col">
                                <p className="position"><strong>WR</strong></p>
                                <p>{startingWR.first_name} {startingWR.last_name}</p>
                                <p>({startingWR.nfl_team})</p>
                            </div>
                        )}
                        {startingTE && (
                            <div className="player-col">
                                <p className="position"><strong>TE</strong></p>
                                <p>{startingTE.first_name} {startingTE.last_name}</p>
                                <p>({startingTE.nfl_team})</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <>
            <h2>Next Matchup:</h2>
            {nextMatchup ? (
                renderMatchupDetails(nextMatchup, true)
            ) : (
                <p>No upcoming matchups</p>
            )}
            
            {upcomingMatchups.length > 0 && (
                <>
                    <h2>Upcoming Matchups:</h2>
                    <div>
                        {upcomingMatchups.map((matchup) => 
                            renderMatchupDetails(matchup, false)
                        )}
                    </div>
                </>
            )}
        </>
    )
}

export default CurrentMatchups;