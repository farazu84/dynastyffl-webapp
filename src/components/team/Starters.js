import PlayerItem from './../../components/team/PlayerItem'


const Starters = ( {starters} ) => {
    return (
        <>
            <h2>Starters:</h2>
            <ul>
                {starters.map((player) => (
                    <PlayerItem key={player.player_id} player={player} />
                ))}
            </ul>
        </>
    )
}

export default Starters