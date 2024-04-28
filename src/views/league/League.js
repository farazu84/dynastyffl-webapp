import { useState, useEffect } from 'react';
import TeamItem from './../../components/league/TeamItem'
import '../../styles/League.css'

const League = () => {

    const [teams, setTeams] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
        const fetchTeams = async () => {
            try{
                const response = await fetch('teams');
                const leagueTeams = await response.json()
                setTeams(leagueTeams.teams);
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
            <ul className="teamList">
                {teams.map((team) => (
                    <TeamItem key={team.team_id} team={team} />
                ))}
            </ul>
        </main>
    )
}

export default League