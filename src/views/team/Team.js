import { useState, useEffect } from 'react';
import { useParams } from "react-router-dom";
import PlayerItem from './../../components/team/PlayerItem'
import '../../styles/Team.css'


const Team = ( ) => {
    const { teamId } = useParams()
    const [pickedTeam, setTeam] = useState({});
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
        const fetchTeam = async () => {
            try{
                const response = await fetch(`${teamId}`);
                const selectedTeam = await response.json()
                setTeam(selectedTeam.team);
                setFetchError(null);
            } catch (error) {
                setFetchError(error.message)
            } finally {
                setIsLoading(false);
            }
        }
    
        fetchTeam()
    }, [])

    return (
        <main>
            <h2 className="title-card">{pickedTeam.team_name}</h2>
            <ul>
                {pickedTeam?.players?.map((player) => (
                    <PlayerItem key={player.player_id} player={player} />
                ))}
            </ul>
        </main>
    )
}

export default Team