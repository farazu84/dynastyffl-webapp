import { Link } from 'react-router-dom';


const TeamItem = ( { team }) => {

    return (
        <li className="team" key={team.team_id}>
            <Link to={`/teams/${team.team_id}`} className="team-link">
                <p>{team.team_name}</p>
            </Link>
        </li>

    )
}

export default TeamItem