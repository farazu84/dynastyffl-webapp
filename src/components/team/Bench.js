import PlayerItem from './../../components/team/PlayerItem'


const Bench = ( {benchPlayers} ) => {
    return (
        <>
            <h2>Bench:</h2>
            <ul>
                {benchPlayers.map((player) => (
                    <PlayerItem key={player.player_id} player={player} />
                ))}
            </ul>
        </>
    )
}

export default Bench