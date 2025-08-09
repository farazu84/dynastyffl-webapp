import { Link } from 'react-router-dom';


const TeamItem = ( { team }) => {

    return (
        <Link to={`/teams/${team.team_id}`}>
            <li className="team" key={team.team_id}>
                <p>{team.team_name}</p>
            </li>
        </Link>

    )
}

export default TeamItem