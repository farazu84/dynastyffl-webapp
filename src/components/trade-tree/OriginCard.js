import React, { useMemo } from 'react';
import PlayerChip from './PlayerChip';
import { formatDate, formatPickLong } from '../../utils/formatters';

const STAT_ROWS = [
    { label: 'Total Pts', key: 'starter_points', decimals: 1 },
    { label: 'Games Started', key: 'games_started', decimals: 0 },
    { label: 'Pts / Start', key: 'ppg', decimals: 1 },
];

const OriginCard = ({ origin, teams = {} }) => {
    const sides = useMemo(() => {
        const teamMap = new Map();

        const ensureTeam = (rosterId, teamName) => {
            if (!teamMap.has(rosterId)) {
                teamMap.set(rosterId, {
                    rosterId,
                    teamName: teamName || `Roster ${rosterId}`,
                    players: [],
                    picks: [],
                });
            }
            return teamMap.get(rosterId);
        };

        (origin.roster_moves || []).forEach(rm => {
            ensureTeam(rm.sleeper_roster_id, rm.team?.team_name);
        });
        (origin.player_moves || []).forEach(pm => {
            if (pm.action === 'add') {
                ensureTeam(pm.sleeper_roster_id, pm.team?.team_name).players.push(
                    pm.player || { first_name: 'Player', last_name: pm.player_sleeper_id, position: null }
                );
            }
        });
        (origin.draft_pick_moves || []).forEach(dp => {
            if (dp.owner_id) {
                ensureTeam(dp.owner_id, dp.team?.team_name).picks.push(dp);
            }
        });

        return Array.from(teamMap.values()).filter(
            t => t.players.length > 0 || t.picks.length > 0
        );
    }, [origin]);

    const totalsFor = (rosterId) => teams[rosterId]?.production_totals || null;

    // The head-to-head stat table only makes sense for a two-sided trade with real production.
    const showStats = useMemo(() => {
        if (sides.length !== 2) return false;
        return sides.some(s => (totalsFor(s.rosterId)?.starter_points || 0) > 0);
    }, [sides, teams]); // eslint-disable-line react-hooks/exhaustive-deps

    const statValue = (totals, key, decimals) => {
        if (!totals || totals.games_started <= 0) return '—';
        return Number(totals[key]).toLocaleString('en-US', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals,
        });
    };

    return (
        <div className="origin-card">
            <div className="origin-card-header">
                <span className="origin-card-badge">ORIGIN TRANSACTION</span>
                <span className="origin-card-date">{formatDate(origin.created_at)}</span>
            </div>

            <div className="origin-card-teams">
                {sides.map((team) => (
                    <div className="origin-card-team" key={team.rosterId}>
                        <span className="origin-card-team-name">{team.teamName}</span>
                        <div className="origin-card-assets">
                            {team.players.map((p, i) => (
                                <PlayerChip key={i} player={p} />
                            ))}
                            {team.picks.map((dp, i) => (
                                <span className="origin-card-pick" key={`pick-${i}`}>
                                    {formatPickLong(dp)}
                                </span>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {showStats && (
                <div className="origin-card-stats">
                    <div className="origin-stat-row origin-stat-head">
                        <span className="origin-stat-left">{sides[0].teamName}</span>
                        <span className="origin-stat-label">Stat</span>
                        <span className="origin-stat-right">{sides[1].teamName}</span>
                    </div>
                    {STAT_ROWS.map(({ label, key, decimals }) => (
                        <div className="origin-stat-row" key={key}>
                            <span className="origin-stat-left origin-stat-value">
                                {statValue(totalsFor(sides[0].rosterId), key, decimals)}
                            </span>
                            <span className="origin-stat-label">{label}</span>
                            <span className="origin-stat-right origin-stat-value">
                                {statValue(totalsFor(sides[1].rosterId), key, decimals)}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

OriginCard.displayName = 'OriginCard';

export default React.memo(OriginCard);
