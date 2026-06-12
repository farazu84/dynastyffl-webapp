import React from 'react';

const Schedule = ({ matchups }) => {
    if (!matchups || matchups.length === 0) {
        return (
            <div className="sched-card">
                <div className="sched-header">
                    <span className="sched-header-title">Schedule</span>
                </div>
                <hr className="nm-divider" />
                <div style={{ padding: '16px', textAlign: 'center' }}>
                    <p style={{ color: 'var(--muted)', fontFamily: 'var(--mono)', fontSize: '0.7rem', letterSpacing: '.1em', textTransform: 'uppercase' }}>
                        No remaining matchups
                    </p>
                </div>
            </div>
        );
    }

    const firstWeek = matchups[0].week;
    const lastWeek = matchups[matchups.length - 1].week;
    const weekRange = firstWeek === lastWeek
        ? `Wk ${String(firstWeek).padStart(2, '0')}`
        : `Wk ${String(firstWeek).padStart(2, '0')}-${String(lastWeek).padStart(2, '0')}`;

    const getAvgScore = (record) => {
        if (!record) return null;
        const gamesPlayed = record.wins + record.losses;
        if (gamesPlayed === 0) return null;
        return (record.points_for / gamesPlayed).toFixed(2);
    };

    return (
        <div className="sched-card">
            {/* Header */}
            <div className="sched-header">
                <span className="sched-header-title">Schedule</span>
                <span className="sched-header-range">Remaining · {weekRange}</span>
            </div>

            {/* Rows */}
            <div className="sched-list">
                {matchups.map((matchup) => {
                    const opponent = matchup.opponent_team;
                    const owner = opponent?.team_owners?.[0]?.user?.user_name ?? 'Unknown';
                    const record = opponent?.current_team_record;
                    const avg = getAvgScore(record);

                    return (
                        <div key={matchup.matchup_id} className="sched-row">
                            <span className="sched-week">
                                {String(matchup.week).padStart(2, '0')}
                            </span>

                            <div className="sched-info">
                                <span className="sched-team-name">
                                    {opponent?.team_name ?? 'Unknown Team'}
                                </span>
                                <span className="sched-team-sub">
                                    {owner}{avg ? ` · Avg ${avg}` : ''}
                                </span>
                            </div>

                            {record && (
                                <div className="sched-badge">
                                    <span className="sched-badge-wins">{record.wins}</span>
                                    <span className="sched-badge-dot">·</span>
                                    <span className="sched-badge-losses">{record.losses}</span>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default Schedule;
