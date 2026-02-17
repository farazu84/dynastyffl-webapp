import React from 'react';

const PlayerChip = ({ player }) => {
    const posClass = player.position ? `player-chip-pos-${player.position.toLowerCase()}` : '';

    return (
        <span className="player-chip">
            <span className="player-chip-name">
                {player.first_name} {player.last_name}
            </span>
            {player.position && (
                <span className={`player-chip-pos ${posClass}`}>
                    {player.position}
                </span>
            )}
        </span>
    );
};

PlayerChip.displayName = 'PlayerChip';

export default React.memo(PlayerChip);
