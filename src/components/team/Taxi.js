import PlayerItem from './../../components/team/PlayerItem'


const Taxi = ( {taxiSquad} ) => {
    return (
        <>
            <h2>Taxi Squad:</h2>
            <ul>
                {taxiSquad.map((player) => (
                    <PlayerItem key={player.player_id} player={player} />
                ))}
            </ul>
        </>
    )
}

export default Taxi