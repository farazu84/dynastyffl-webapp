import { useState, useEffect, useMemo } from 'react';
import TeamItem from './../../components/league/TeamItem';
import ArticleHeader from './../../components/league/ArticleHeader';
import TrendingPlayers from './../../components/league/TrendingPlayers';
import '../../styles/League.css';
import MatchupItem from './../../components/league/MatchupItem';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';

const League = () => {

    const [teams, setTeams] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [matchups, setMatchups] = useState([]);
    
    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);
                
                const [teamsResponse, matchupsResponse] = await Promise.all([
                    cachedFetch(`${config.API_BASE_URL}/teams`),
                    cachedFetch(`${config.API_BASE_URL}/matchups/current_matchups`)
                ]);
                
                if (!teamsResponse.ok) throw new Error(`Teams API error: ${teamsResponse.status}`);
                if (!matchupsResponse.ok) throw new Error(`Matchups API error: ${matchupsResponse.status}`);
                
                // Parse responses in parallel
                const [teamsData, matchupsData] = await Promise.all([
                    teamsResponse.json(),
                    matchupsResponse.json()
                ]);
                
                setTeams(teamsData.teams || []);
                setMatchups(matchupsData.matchups || []);
                
            } catch (error) {
                setFetchError(error.message);
                setTeams([]);
                setMatchups([]);
            } finally {
                setIsLoading(false);
            }
        };
    
        fetchData();
    }, [])

    const memoizedTeams = useMemo(() => {
        return teams.map((team) => (
            <TeamItem key={team.team_id} team={team} />
        ));
    }, [teams]);

    const memoizedMatchups = useMemo(() => {
        return matchups.map((matchup) => (
            <MatchupItem key={matchup.matchup_id} matchup={matchup} />
        ));
    }, [matchups]);

    const errorDisplay = useMemo(() => {
        if (!fetchError) return null;
        return (
            <div className="league-error" style={{ 
                color: '#f44336', 
                background: '#2a2a2a', 
                padding: '10px', 
                borderRadius: '4px', 
                margin: '10px 0' 
            }}>
                Error loading data: {fetchError}
            </div>
        );
    }, [fetchError]);

    if (isLoading) {
        return (
            <main>
                <div className="league-main-container" style={{ textAlign: 'center', padding: '40px' }}>
                    <div style={{ color: '#61dafb', fontSize: '1.2em' }}>
                        Loading league data...
                    </div>
                </div>
            </main>
        );
    }

    return (
        <main>
            <div className="league-main-container">
                <div className="league-left-content">
                    <ArticleHeader />
                    <div className="current-matchups-section">
                        <h2>Current Matchups</h2>
                        {memoizedMatchups}
                        {errorDisplay}
                    </div>
                </div>
                <div className="league-standings-sidebar">
                    <div className="standings-header">
                        <h2>Team Standings</h2>
                    </div>
                    <ul className="teamList">
                        {memoizedTeams}
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