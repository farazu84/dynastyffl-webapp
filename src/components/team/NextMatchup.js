import React from 'react';

const NextMatchup = ({ matchup }) => {
    if (!matchup) {
        return (
            <div className="nm-card">
                <div className="nm-header">
                    <span className="nm-header-title">Next Matchup</span>
                </div>
                <hr className="nm-divider" />
                <div style={{ padding: '16px', textAlign: 'center' }}>
                    <p style={{ color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: '0.7rem', letterSpacing: '.1em', textTransform: 'uppercase' }}>
                        No upcoming matchup
                    </p>
                </div>
            </div>
        );
    }

    const opponent = matchup.opponent_team;
    const team = matchup.team;

    const opponentOwner = opponent?.team_owners?.[0]?.user?.user_name ?? 'Unknown';
    const opponentRecord = opponent?.current_team_record;
    const teamRecord = team?.current_team_record;

    const formatRecord = (record) => {
        if (!record) return null;
        return `${record.wins}-${record.losses}`;
    };

    const getPoints = (pts) => {
        if (pts === null || pts === undefined || pts === 0) return null;
        return pts.toFixed(1);
    };

    const getStarter = (players, position) =>
        players?.find(p => p.position === position && p.starter === true) ?? null;

    const opponentPlayers = opponent?.players ?? [];
    const starters = [
        { pos: 'QB', player: getStarter(opponentPlayers, 'QB') },
        { pos: 'RB', player: getStarter(opponentPlayers, 'RB') },
        { pos: 'WR', player: getStarter(opponentPlayers, 'WR') },
        { pos: 'TE', player: getStarter(opponentPlayers, 'TE') },
    ];

    const teamPts = getPoints(matchup.points_for);
    const opponentPts = getPoints(matchup.points_against);

    return (
        <div className="nm-card">
            {/* Header */}
            <div className="nm-header">
                <span className="nm-header-title">Next Matchup</span>
            </div>
            <hr className="nm-divider" />

            {/* Subheader */}
            <div className="nm-subheader">
                <span className="nm-week">Week {String(matchup.week).padStart(2, '0')}</span>
                {matchup.completed && (
                    <span className="nm-lock" style={{ color: 'var(--green)' }}>Final</span>
                )}
                {!matchup.completed && teamPts && (
                    <span className="nm-lock" style={{ color: 'var(--gold)' }}>In Progress</span>
                )}
            </div>
            <hr className="nm-divider" />

            {/* Teams */}
            <div className="nm-teams">
                <div className="nm-team">
                    <span className="nm-team-label">You</span>
                    <span className="nm-team-name">{team?.team_name ?? 'Your Team'}</span>
                    <span className="nm-team-meta">
                        {formatRecord(teamRecord)}
                        {teamPts && ` · ${teamPts} pts`}
                    </span>
                </div>

                <div className="nm-vs-badge">VS</div>

                <div className="nm-team">
                    <span className="nm-team-label">Owner {opponentOwner}</span>
                    <span className="nm-team-name">{opponent?.team_name ?? 'Opponent'}</span>
                    <span className="nm-team-meta">
                        {formatRecord(opponentRecord)}
                        {opponentPts && ` · ${opponentPts} pts`}
                    </span>
                </div>
            </div>

            {/* Opponent key starters */}
            {starters.some(s => s.player) && (
                <div className="nm-starters">
                    {starters.map(({ pos, player }) => (
                        <div key={pos} className="nm-starter-chip">
                            <span className="nm-starter-pos">{pos}</span>
                            {player ? (
                                <>
                                    <span className="nm-starter-name">
                                        {player.first_name[0]}. {player.last_name}
                                    </span>
                                    <span className="nm-starter-team">{player.nfl_team}</span>
                                </>
                            ) : (
                                <span className="nm-starter-name" style={{ color: 'var(--mute-dim)' }}>—</span>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default NextMatchup;
