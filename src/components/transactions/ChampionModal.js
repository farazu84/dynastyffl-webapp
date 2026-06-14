import React, { useState, useEffect } from 'react';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/ChampionModal.css';

const fmt = (n) => (n == null ? '—' : Number(n).toFixed(1));

const PositionChip = ({ position }) => {
    if (!position) return null;
    return (
        <span className={`player-chip-pos player-chip-pos-${position.toLowerCase()}`}>
            {position}
        </span>
    );
};

const ChampionModal = ({ year, onClose }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        let active = true;
        const fetchRun = async () => {
            setLoading(true);
            setError(false);
            try {
                const res = await cachedFetch(`${config.API_BASE_URL}/teams/champions/${year}`);
                if (!res.ok) throw new Error('failed');
                const json = await res.json();
                if (active) setData(json);
            } catch {
                if (active) setError(true);
            } finally {
                if (active) setLoading(false);
            }
        };
        fetchRun();
        return () => { active = false; };
    }, [year]);

    const champion = data?.champion;
    const franchise = data?.franchise;
    const ownerName = champion?.owners?.map(o => o.user_name).filter(Boolean).join(', ');

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal modal-wide champion-modal" onClick={e => e.stopPropagation()}>
                <button className="modal-close" onClick={onClose}>✕</button>

                {loading && <p className="champion-modal-status">Loading…</p>}
                {error && <p className="champion-modal-status">Couldn’t load this championship.</p>}

                {!loading && !error && champion && (
                    <>
                        {/* ── Header ─────────────────────────────────────── */}
                        <div className="champion-modal-header">
                            <span className="champion-modal-year">{champion.year}</span>
                            <h2>{champion.team_name}</h2>
                            {ownerName && <p className="champion-modal-owner">{ownerName}</p>}
                            <div className="champion-modal-meta">
                                {franchise?.seed != null && <span>{ordinal(franchise.seed)} seed</span>}
                                {champion.season_record && (
                                    <span>{champion.season_record.wins}–{champion.season_record.losses}</span>
                                )}
                                {franchise?.championships != null && (
                                    <span className="champion-modal-rings">🏆 ×{franchise.championships}</span>
                                )}
                            </div>
                        </div>

                        {/* ── Bracket ────────────────────────────────────── */}
                        {data.bracket?.length > 0 && (
                            <section className="champion-section">
                                <h3>Path to the Title</h3>
                                <div className="champion-bracket">
                                    {data.bracket.map((round) => (
                                        <div className="champion-bracket-round" key={round.round}>
                                            <span className="champion-bracket-round-label">
                                                {roundLabel(round.round, data.bracket.length)}
                                            </span>
                                            {round.matchups.map((m) => (
                                                <BracketGame key={m.sleeper_matchup_id} game={m} champRoster={champRoster(data)} />
                                            ))}
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}

                        {/* ── Notable starters + Biggest performances (side by side) ── */}
                        {(data.notable_starters?.length > 0 || data.big_performances?.length > 0) && (
                            <div className="champion-section-row">
                                {data.notable_starters?.length > 0 && (
                                    <section className="champion-section">
                                        <h3>Notable Starters</h3>
                                        <ul className="champion-list">
                                            {data.notable_starters.map((p, i) => (
                                                <li key={`${p.name}-${i}`} className="champion-list-row">
                                                    <span className="champion-list-rank">{i + 1}</span>
                                                    <span className="champion-list-name">{p.name}</span>
                                                    <PositionChip position={p.position} />
                                                    {p.nfl_team && <span className="champion-list-sub">{p.nfl_team}</span>}
                                                    <span className="champion-list-pts">
                                                        {fmt(p.total_points)}
                                                        <span className="champion-list-pts-label">
                                                            {p.games_played === 1 ? ' pt' : ' pts'}
                                                        </span>
                                                    </span>
                                                </li>
                                            ))}
                                        </ul>
                                    </section>
                                )}

                                {data.big_performances?.length > 0 && (
                                    <section className="champion-section">
                                        <h3>Biggest Performances</h3>
                                        <ul className="champion-list">
                                            {data.big_performances.map((p, i) => (
                                                <li key={`${p.name}-${p.week}-${i}`} className="champion-list-row">
                                                    <span className="champion-list-name">{p.name}</span>
                                                    <PositionChip position={p.position} />
                                                    <span className="champion-list-sub">
                                                        Wk {p.week}{p.opponent_team_name ? ` vs ${p.opponent_team_name}` : ''}
                                                    </span>
                                                    <span className="champion-list-pts champion-list-pts-hot">{fmt(p.points)}</span>
                                                </li>
                                            ))}
                                        </ul>
                                    </section>
                                )}
                            </div>
                        )}

                        {/* ── Title-game box score ───────────────────────── */}
                        {data.title_game?.starters?.length > 0 && (
                            <section className="champion-section">
                                <h3>Championship Box Score</h3>
                                <div className="champion-boxscore-final">
                                    <span className="champion-boxscore-team">{champion.team_name}</span>
                                    <span className="champion-boxscore-score">
                                        {fmt(data.title_game.points_for)} – {fmt(data.title_game.points_against)}
                                    </span>
                                    <span className="champion-boxscore-team champion-boxscore-opp">
                                        {data.title_game.opponent_team_name || 'Opponent'}
                                    </span>
                                </div>
                                <ul className="champion-list champion-boxscore-list">
                                    {data.title_game.starters.map((s, i) => (
                                        <li key={`${s.name}-${i}`} className="champion-list-row">
                                            <span className="champion-list-name">{s.name}</span>
                                            <PositionChip position={s.position} />
                                            <span className="champion-list-pts">{fmt(s.points)}</span>
                                        </li>
                                    ))}
                                </ul>
                            </section>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};

// Champion roster id is the winner of the flagged championship game.
const champRoster = (data) => {
    for (const round of data.bracket || []) {
        for (const m of round.matchups) {
            if (m.is_championship) return m.winner_roster_id;
        }
    }
    return null;
};

const BracketGame = ({ game, champRoster: cr }) => {
    const teamWon = game.winner_roster_id != null && game.team.roster_id === game.winner_roster_id;
    const oppWon = game.winner_roster_id != null && game.opponent.roster_id === game.winner_roster_id;
    const label = placementLabel(game);
    return (
        <div className={`champion-bracket-game${game.is_championship ? ' is-championship' : ''}`}>
            {label && (
                <span className={`champion-bracket-game-label${game.is_championship ? ' is-championship' : ''}`}>
                    {label}
                </span>
            )}
            <BracketSide side={game.team} won={teamWon} isChamp={game.team.roster_id === cr} />
            <BracketSide side={game.opponent} won={oppWon} isChamp={game.opponent.roster_id === cr} />
        </div>
    );
};

const BracketSide = ({ side, won, isChamp }) => (
    <div className={`champion-bracket-side${won ? ' won' : ''}${isChamp ? ' is-champ' : ''}`}>
        {side.seed != null && <span className="champion-bracket-seed">{side.seed}</span>}
        <span className="champion-bracket-name">{side.name || 'TBD'}</span>
        <span className="champion-bracket-pts">{fmt(side.points)}</span>
    </div>
);

// Placement games carry a `placement` value (the spot they decide): 1 = title,
// 3 = 3rd-place game, 5 = 5th-place game, etc. Early-round games have none.
const placementLabel = (game) => {
    if (game.is_championship || game.placement === 1) return 'Championship';
    if (game.placement == null) return null;
    return `${ordinal(game.placement)} Place`;
};

const ordinal = (n) => {
    const s = ['th', 'st', 'nd', 'rd'];
    const v = n % 100;
    return n + (s[(v - 20) % 10] || s[v] || s[0]);
};

// Last round is the final; second-to-last the semis; otherwise "Round N".
const roundLabel = (round, totalRounds) => {
    if (round === totalRounds) return 'Final';
    if (round === totalRounds - 1) return 'Semifinals';
    if (round === totalRounds - 2) return 'Quarterfinals';
    return `Round ${round}`;
};

export default ChampionModal;
