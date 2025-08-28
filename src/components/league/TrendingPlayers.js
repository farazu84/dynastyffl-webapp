import React from 'react';

const TrendingPlayers = () => {
    return (
        <div className="trending-players-container">
            <h3>Trending Players</h3>
            <div className="trending-players-embed">
                <iframe 
                    src="https://sleeper.app/embed/players/nfl/trending/add?lookback_hours=10&limit=25" 
                    width="100%" 
                    height="500" 
                    allowtransparency="true" 
                    frameborder="0"
                    title="Sleeper Trending Players"
                >
                </iframe>
            </div>
        </div>
    );
};

export default TrendingPlayers;
