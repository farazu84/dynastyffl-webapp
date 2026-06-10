import React from 'react';
import '../../styles/ScoreboardStrip.css';

const ScoreboardStrip = React.memo(({ matchups }) => {
    if (!matchups || matchups.length === 0) return null;

    const formatScore = (score) => {
        return score !== undefined && score !== null ? score.toFixed(1) : '—';
    };

    return (
        <div className="scoreboard-strip">
            <div className="scoreboard-strip-inner">
                <div className="scoreboard-strip-grid">
                    {matchups.map((matchup) => {
                        const teamScore = matchup.points_for;
                        const opponentScore = matchup.points_against;
                        const hasScores = teamScore !== undefined && teamScore !== null &&
                                          opponentScore !== undefined && opponentScore !== null;
                        const teamWinning = hasScores && teamScore > opponentScore;
                        const opponentWinning = hasScores && opponentScore > teamScore;
                        const live = !matchup.completed;

                        return (
                            <div className="scoreboard-strip-card" key={matchup.matchup_id}>
                                <div className={`strip-row ${live ? 'live' : ''}`}>
                                    <span className="strip-name">{matchup.team?.team_name || 'TBD'}</span>
                                    <span className={`strip-score ${teamWinning ? 'win' : (opponentWinning ? 'lose' : '')}`}>
                                        {formatScore(teamScore)}
                                    </span>
                                </div>
                                <div className={`strip-row ${live ? 'live' : ''}`}>
                                    <span className="strip-name">{matchup.opponent_team?.team_name || 'TBD'}</span>
                                    <span className={`strip-score ${opponentWinning ? 'win' : (teamWinning ? 'lose' : '')}`}>
                                        {formatScore(opponentScore)}
                                    </span>
                                </div>
                                <div className="strip-status">
                                    {live ? (
                                        <span className="strip-live"><span className="strip-dot"></span>LIVE</span>
                                    ) : (
                                        <span>FINAL</span>
                                    )}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
});

ScoreboardStrip.displayName = 'ScoreboardStrip';

export default ScoreboardStrip;
