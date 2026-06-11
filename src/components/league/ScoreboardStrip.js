import React from 'react';
import '../../styles/ScoreboardStrip.css';

// Thu=4, Fri=5, Sat=6, Sun=0, Mon=1
const GAME_DAYS = new Set([4, 5, 6, 0, 1]);

const ScoreboardStrip = React.memo(({ matchups, leagueState }) => {
    if (!matchups || matchups.length === 0) return null;

    const rawWeek = leagueState?.current_week ?? null;
    const week = rawWeek === 0 ? 1 : rawWeek;
    const year = leagueState?.current_year ?? null;

    const day = new Date().getDay();
    const isGameDay = GAME_DAYS.has(day) && week >= 1 && week <= 20;

    const formatScore = (score) =>
        score !== undefined && score !== null ? score.toFixed(1) : '—';

    return (
        <div className="scoreboard-strip">
            <div className="scoreboard-strip-inner">
                {week && year && (
                    <div className="scoreboard-strip-meta">
                        <span className="scoreboard-strip-week">Week {week}</span>
                        <span className="scoreboard-strip-year">{year}</span>
                    </div>
                )}
                <div
                    className="scoreboard-strip-grid"
                    style={{ gridTemplateColumns: `repeat(${matchups.length}, 1fr)` }}
                >
                    {matchups.map((matchup) => {
                        const teamScore = matchup.points_for;
                        const opponentScore = matchup.points_against;
                        const hasScores = teamScore !== undefined && teamScore !== null &&
                                          opponentScore !== undefined && opponentScore !== null;
                        const teamWinning = hasScores && teamScore > opponentScore;
                        const opponentWinning = hasScores && opponentScore > teamScore;
                        const completed = matchup.completed;
                        const showLive = !completed && isGameDay;

                        const teamRecord = matchup.team?.current_team_record;
                        const oppRecord = matchup.opponent_team?.current_team_record;
                        const fmtRecord = (r) => r ? ` (${r.wins}-${r.losses})` : '';

                        return (
                            <div className="scoreboard-strip-card" key={matchup.matchup_id}>
                                <div className={`strip-row ${showLive ? 'live' : ''}`}>
                                    <span className="strip-name">
                                        {matchup.team?.team_name || 'TBD'}
                                        <span className="strip-record">{fmtRecord(teamRecord)}</span>
                                    </span>
                                    <span className={`strip-score ${teamWinning ? 'win' : (opponentWinning ? 'lose' : '')}`}>
                                        {formatScore(teamScore)}
                                    </span>
                                </div>
                                <div className={`strip-row ${showLive ? 'live' : ''}`}>
                                    <span className="strip-name">
                                        {matchup.opponent_team?.team_name || 'TBD'}
                                        <span className="strip-record">{fmtRecord(oppRecord)}</span>
                                    </span>
                                    <span className={`strip-score ${opponentWinning ? 'win' : (teamWinning ? 'lose' : '')}`}>
                                        {formatScore(opponentScore)}
                                    </span>
                                </div>
                                <div className="strip-status">
                                    {completed ? (
                                        <span>FINAL</span>
                                    ) : showLive ? (
                                        <span className="strip-live"><span className="strip-dot"></span>LIVE</span>
                                    ) : (
                                        <span className="strip-preview">PREVIEW</span>
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
