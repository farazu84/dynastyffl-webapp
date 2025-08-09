import { useState, useEffect } from 'react';
import { useParams } from "react-router-dom";
import PlayerItem from './../../components/team/PlayerItem'
import Starters from './../../components/team/Starters'
import Bench from './../../components/team/Bench'
import Taxi from './../../components/team/Taxi'
import TeamHeader from './../../components/team/TeamHeader'



import '../../styles/Team.css'


const Team = ( ) => {
    const { teamId } = useParams()
    const [pickedTeam, setTeam] = useState({});
    const [starters, setStarters] = useState([])
    const [bench, setBench] = useState([]);
    const [taxi, setTaxi] = useState([]);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    
    useEffect(() => {
        const fetchTeam = async () => {
            try{
                const response = await fetch(`${teamId}`);
                const selectedTeam = await response.json()
                const teamStarters = selectedTeam.team.players.filter(player  => player.starter === true)
                const teamBench = selectedTeam.team.players.filter(player  => player.taxi === false && player.starter === false)
                const teamTaxi = selectedTeam.team.players.filter(player  => player.taxi === true)
                setTeam(selectedTeam.team);
                setStarters(teamStarters);
                setBench(teamBench);
                setTaxi(teamTaxi);
                console.log(bench)
                setFetchError(null);
            } catch (error) {
                setFetchError(error.message)
            } finally {
                setIsLoading(false);
            }
        }
    
        fetchTeam()
    }, [])

    //const starters = pickedTeam?.players?.filter(player  => player.starter === true)
    /*
    const taxi = pickedTeam?.players?.filter(player  => player.taxi === true)
    const bench = pickedTeam?.players?.filter(player  => player.taxi === false && player.starter === false)
    console.log(starters)
                <ul>
                {pickedTeam?.players?.map((player) => (
                    <PlayerItem key={player.player_id} player={player} />
                ))}
            </ul>
    */
    return (
        <main>
            <TeamHeader team={pickedTeam} />
            <Starters starters={starters} />
            <Bench benchPlayers={bench} />
            <Taxi taxiSquad={taxi} />
        </main>
    )
}

export default Team