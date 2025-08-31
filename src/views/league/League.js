import { useState, useEffect } from 'react';
import TeamItem from './../../components/league/TeamItem';
import ArticleHeader from './../../components/league/ArticleHeader';
import '../../styles/League.css';
import MatchupItem from './../../components/league/MatchupItem';
import config from '../../config';

const League = () => {

    const [teams, setTeams] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [matchups, setMatchups] = useState([]);
    
    useEffect(() => {
        const fetchTeams = async () => {
            try{
                const response = await fetch(`${config.API_BASE_URL}/teams`);
                const matchupsResponse = await fetch(`${config.API_BASE_URL}/matchups/1`);
                const matchups = await matchupsResponse.json();
                console.log(matchups);
                const leagueTeams = await response.json()
                setTeams(leagueTeams.teams);
                setMatchups(matchups.matchups);
                setFetchError(null);
                console.log(leagueTeams)
            } catch (error) {
                setFetchError(error.message)
            } finally {
                setIsLoading(false);
            }
        }
    
        fetchTeams()
    }, [])

    return (
        <main>
            <ArticleHeader />
            <div className="league-content-split" style={{ display: 'flex', flexDirection: 'row', gap: '20px', width: '100%' }}>
                <div className="league-left-section" style={{ flex: 1, width: '50%', maxWidth: '50%' }}>
                    <h2>Team Standings</h2>
                    <ul className="teamList">
                        {teams.map((team) => (
                            <TeamItem key={team.team_id} team={team} />
                        ))}
                    </ul>
                </div>
                <div className="league-right-section" style={{ flex: 1, width: '50%', maxWidth: '50%' }}>
                    <h2>Week 1 Matchups</h2>
                    {matchups.map((matchup) => (
                        <MatchupItem key={matchup.matchup_id} matchup={matchup} />
                    ))}
                </div>
            </div>
        </main>
    )
}

export default League