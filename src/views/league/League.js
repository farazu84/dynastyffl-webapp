import { useState, useEffect } from 'react';
import TeamItem from './../../components/league/TeamItem';
import ArticleHeader from './../../components/league/ArticleHeader';
import TrendingPlayers from './../../components/league/TrendingPlayers';
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
                const matchupsResponse = await fetch(`${config.API_BASE_URL}/matchups/current_matchups`);
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
            <div className="league-main-container">
                <div className="league-left-content">
                    <ArticleHeader />
                    <div className="current-matchups-section">
                        <h2>Current Matchups</h2>
                        {matchups.map((matchup) => (
                            <MatchupItem key={matchup.matchup_id} matchup={matchup} />
                        ))}
                    </div>
                </div>
                <div className="league-standings-sidebar">
                    <div className="standings-header">
                        <h2>Team Standings</h2>
                    </div>
                    <ul className="teamList">
                        {teams.map((team) => (
                            <TeamItem key={team.team_id} team={team} />
                        ))}
                    </ul>
                    <div className="sidebar-trending-players">
                        <TrendingPlayers />
                    </div>
                </div>
            </div>
        </main>
    )
}

export default League