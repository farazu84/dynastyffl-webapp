const MatchupItem = ( {matchup} ) => {
    const getStartingPlayer = (team, position) => {
        if (!team.players) return null;
        return team.players.find(player => 
            player.position === position && player.starter === true
        );
    };

    const getTeamOwner = (team) => {
        if (!team.team_owners || team.team_owners.length === 0) return 'Unknown Owner';
        return team.team_owners[0].user.user_name;
    };

    const renderTeamInfo = (team, isLeft = true) => {
        if (!team) return <div>Team data not available</div>;

        const owner = getTeamOwner(team);
        const startingQB = getStartingPlayer(team, 'QB');
        const startingRB = getStartingPlayer(team, 'RB');
        const startingWR = getStartingPlayer(team, 'WR');
        const startingTE = getStartingPlayer(team, 'TE');

        return (
            <div className="matchup-team">
                <h3>{team.team_name}</h3>
                <div className="player-row">
                    <div className="player-col">
                        <p><strong>Owner:</strong> {owner}</p>
                        <p><strong>Record:</strong> {team.record || '0-0'}</p>
                        <p><strong>Avg Starter Age:</strong> {team.average_starter_age || 'N/A'}</p>
                    </div>
                </div>
                
                <div className="player-col" style={{ marginTop: '10px' }}>
                    <h3>Key Starters:</h3>
                    <div className="player-row" style={{ flexWrap: 'nowrap', gap: '8px', justifyContent: 'flex-start' }}>
                        {startingQB && (
                            <div className="matchup-player-col">
                                <p className="matchup-player-position">QB</p>
                                <p className="matchup-player-name">{startingQB.first_name} {startingQB.last_name}</p>
                                <p className="matchup-player-team">({startingQB.nfl_team})</p>
                            </div>
                        )}
                        {startingRB && (
                            <div className="matchup-player-col">
                                <p className="matchup-player-position">RB</p>
                                <p className="matchup-player-name">{startingRB.first_name} {startingRB.last_name}</p>
                                <p className="matchup-player-team">({startingRB.nfl_team})</p>
                            </div>
                        )}
                        {startingWR && (
                            <div className="matchup-player-col">
                                <p className="matchup-player-position">WR</p>
                                <p className="matchup-player-name">{startingWR.first_name} {startingWR.last_name}</p>
                                <p className="matchup-player-team">({startingWR.nfl_team})</p>
                            </div>
                        )}
                        {startingTE && (
                            <div className="matchup-player-col">
                                <p className="matchup-player-position">TE</p>
                                <p className="matchup-player-name">{startingTE.first_name} {startingTE.last_name}</p>
                                <p className="matchup-player-team">({startingTE.nfl_team})</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div key={matchup.matchup_id} className="matchup-card">
            {renderTeamInfo(matchup.team, true)}
            
            <div className="matchup-vs">
                <h2 style={{ color: 'white', margin: '0' }}>VS</h2>
                <p style={{ margin: '5px 0', fontSize: 'small' }}>Week {matchup.week}</p>
            </div>
            
            {renderTeamInfo(matchup.opponent_team, false)}
        </div>
    )
}

export default MatchupItem;