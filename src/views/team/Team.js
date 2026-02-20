import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from "react-router-dom";
import Starters from './../../components/team/Starters'
import Bench from './../../components/team/Bench'
import Taxi from './../../components/team/Taxi'
import TeamHeader from './../../components/team/TeamHeader'
import CurrentMatchups from './../../components/team/CurrentMatchups'
import NewsBar from './../../components/team/NewsBar'
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';

import '../../styles/Team.css'


const Team = React.memo(() => {
    const { teamId } = useParams()
    const [pickedTeam, setTeam] = useState({});
    const [starters, setStarters] = useState([])
    const [bench, setBench] = useState([]);
    const [taxi, setTaxi] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [matchups, setMatchups] = useState([]);
    const [articles, setArticles] = useState([]);

    
    useEffect(() => {
        const fetchTeam = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);
                
                // Parallel API calls for better performance
                const [teamResponse, matchupsResponse] = await Promise.all([
                    cachedFetch(`${config.API_BASE_URL}/teams/${teamId}`),
                    cachedFetch(`${config.API_BASE_URL}/teams/${teamId}/matchups`)
                ]);
                
                if (!teamResponse.ok) throw new Error(`Team API error: ${teamResponse.status}`);
                if (!matchupsResponse.ok) throw new Error(`Matchups API error: ${matchupsResponse.status}`);
                
                const [teamData, matchupsData] = await Promise.all([
                    teamResponse.json(),
                    matchupsResponse.json()
                ]);
                
                const team = teamData.team;
                const players = team.players || [];
                
                // Filter players efficiently
                const teamStarters = players.filter(player => player.starter === true);
                const teamBench = players.filter(player => player.taxi === false && player.starter === false);
                const teamTaxi = players.filter(player => player.taxi === true);
                
                // Set all state at once
                setTeam(team);
                setStarters(teamStarters);
                setBench(teamBench);
                setTaxi(teamTaxi);
                setMatchups(matchupsData.matchups || []);
                setArticles(team.articles || []);
                
            } catch (error) {
                console.error('Team fetch error:', error);
                setFetchError(error.message);
                // Set empty fallbacks
                setTeam({});
                setStarters([]);
                setBench([]);
                setTaxi([]);
                setMatchups([]);
                setArticles([]);
            } finally {
                setIsLoading(false);
            }
        };
    
        if (teamId) {
            fetchTeam();
        }
    }, [teamId])

    // Memoize error display
    const errorDisplay = useMemo(() => {
        if (!fetchError) return null;
        return (
            <div style={{ 
                color: '#f44336', 
                background: '#2a2a2a', 
                padding: '20px', 
                borderRadius: '8px', 
                margin: '20px',
                textAlign: 'center' 
            }}>
                Error loading team data: {fetchError}
            </div>
        );
    }, [fetchError]);

    // Loading state
    if (isLoading) {
        return (
            <main style={{ textAlign: 'center', padding: '40px' }}>
                <div style={{ color: '#61dafb', fontSize: '1.2em' }}>
                    Loading team data...
                </div>
            </main>
        );
    }

    // Error state
    if (fetchError) {
        return <main>{errorDisplay}</main>;
    }

    return (
        <main>
            <TeamHeader team={pickedTeam} />
            <NewsBar articles={articles} />
            <div className="team-content-split">
                <div className="team-left-section">
                    <Starters starters={starters} />
                    <Bench benchPlayers={bench} />
                    <Taxi taxiSquad={taxi} />
                </div>
                <div className="team-right-section">
                    <CurrentMatchups matchups={matchups} />
                </div>
            </div>
        </main>
    );
});

Team.displayName = 'Team';

export default Team;