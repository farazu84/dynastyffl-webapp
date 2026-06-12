import { useState, useEffect, useMemo } from 'react';
import TeamItem from './../../components/league/TeamItem';
import ArticleHeader from './../../components/league/ArticleHeader';
import '../../styles/League.css';
import ScoreboardStrip from './../../components/league/ScoreboardStrip';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';

const League = () => {

    const [teams, setTeams] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [matchups, setMatchups] = useState([]);
    const [leagueState, setLeagueState] = useState(null);
    
    useEffect(() => {
        const fetchData = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);
                
                const [teamsResponse, matchupsResponse, leagueStateResponse] = await Promise.all([
                    cachedFetch(`${config.API_BASE_URL}/teams`),
                    cachedFetch(`${config.API_BASE_URL}/matchups/current_matchups`),
                    cachedFetch(`${config.API_BASE_URL}/league/state`)
                ]);

                if (!teamsResponse.ok) throw new Error(`Teams API error: ${teamsResponse.status}`);
                if (!matchupsResponse.ok) throw new Error(`Matchups API error: ${matchupsResponse.status}`);

                const [teamsData, matchupsData, leagueStateData] = await Promise.all([
                    teamsResponse.json(),
                    matchupsResponse.json(),
                    leagueStateResponse.ok ? leagueStateResponse.json() : Promise.resolve(null)
                ]);

                setTeams(teamsData.teams || []);
                setMatchups(matchupsData.matchups || []);
                setLeagueState(leagueStateData?.success ? leagueStateData : null);
                
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
        return teams.map((team, index) => (
            <TeamItem key={team.team_id} team={team} rank={index + 1} />
        ));
    }, [teams]);

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
            <ScoreboardStrip matchups={matchups} leagueState={leagueState} />
            <div className="league-main-container">
                <div className="league-left-content">
                    <ArticleHeader />
                    {errorDisplay}
                </div>
                <div className="league-standings-sidebar">
                    <div className="standings-header">
                        <h2>Team Standings</h2>
                    </div>
                    <ul className="teamList">
                        {memoizedTeams}
                    </ul>
                </div>
            </div>
        </main>
    )
}

export default League