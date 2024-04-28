import { Link } from 'react-router-dom';


const TeamItem = ( { player }) => {

    return (
        <li className="team" key={player.player_id}>
            <div className="player-row">
                <p className="position">{player.position}</p>
                <div className="player-col">
                    <h3>{player.first_name} {player.last_name}</h3>
                    <p>Team: {player.nfl_team ?? "Free Agent"}</p>
                    <p>Age: {player.age ?? "Unknown"}</p>
                    <p>College: {player.college ?? "Ball So Hard U"}</p>
                </div>
            </div>
        </li>

    )
}

export default TeamItem