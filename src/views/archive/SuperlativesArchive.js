import React, { useState, useEffect, useMemo } from 'react';
import SuperlativeCard from '../../components/transactions/SuperlativeCard';
import Pagination from '../../components/shared/Pagination';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/SuperlativesArchive.css';

// 2 rows of the 3-column desktop grid.
const PER_PAGE = 6;

const PLAYER_KEYS = new Set([
    'boomerang', 'most_dropped', 'most_teams', 'most_traded',
    'startup_loyalists', 'startup_steals', 'rookie_draft_steals',
    'the_franchise',
    'workhorse', 'tenured', 'the_anchor', 'bench_warmers_revenge',
]);

const playerName = (p) => `${p.first_name} ${p.last_name}`;

// "A leads 7-5" / "Even 6-6" from a bad_blood pairing.
const rivalryRecord = (r) => {
    if (r.team_1_wins === r.team_2_wins) return `Even ${r.team_1_wins}-${r.team_2_wins}`;
    return r.team_1_wins > r.team_2_wins
        ? `${r.team_1} leads ${r.team_1_wins}-${r.team_2_wins}`
        : `${r.team_2} leads ${r.team_2_wins}-${r.team_1_wins}`;
};

// Single source of truth for every superlative card. `source` picks which
// endpoint payload to read; `map` turns one row into { name, subtitle?, stat }.
const CATEGORIES = [
    // ── Players ──────────────────────────────────────────────────
    {
        key: 'boomerang', group: 'players', category: 'Players', icon: '↺',
        title: 'Should I Call My Ex?',
        description: 'Players re-added to the same team the most times',
        source: 'players', field: 'boomerang',
        map: (p) => ({ name: playerName(p), subtitle: p.team_name, stat: `${p.times_added}×` }),
    },
    {
        key: 'most_dropped', group: 'players', category: 'Players', icon: '↗',
        title: 'Ghosted',
        description: 'Players dropped the most times across the league',
        source: 'players', field: 'most_dropped',
        map: (p) => ({ name: playerName(p), stat: `${p.drop_count} drops` }),
    },
    {
        key: 'most_teams', group: 'players', category: 'Players', icon: '↻',
        title: 'Making The Rounds',
        description: 'Players rostered by the most different teams',
        source: 'players', field: 'most_teams',
        map: (p) => ({ name: playerName(p), stat: `${p.team_count} teams` }),
    },
    {
        key: 'most_traded', group: 'players', category: 'Players', icon: '⇄',
        title: 'Most Wanted',
        description: 'Players involved in the most trades',
        source: 'players', field: 'most_traded',
        map: (p) => ({ name: playerName(p), stat: `${p.trade_count} trades` }),
    },
    // ── Teams ────────────────────────────────────────────────────
    {
        key: 'frequent_trade_partners', group: 'teams', category: 'Teams', icon: '⇄',
        title: 'Eskimo Brothers',
        description: 'Team pairs that have traded with each other the most',
        source: 'teams', field: 'frequent_trade_partners',
        map: (t) => ({ name: `${t.team_1} + ${t.team_2}`, stat: `${t.trade_count} trades` }),
    },
    {
        key: 'most_trades', group: 'teams', category: 'Teams', icon: '★',
        title: 'The Dealmaker',
        description: 'Teams ranked by total number of trades made',
        source: 'teams', field: 'most_trades',
        map: (t) => ({ name: t.team_name, stat: `${t.trade_count} trades` }),
    },
    {
        key: 'waiver_warriors', group: 'teams', category: 'Teams', icon: '↗',
        title: 'Swipe Right',
        description: 'Teams with the most waiver & free-agent pickups',
        source: 'teams', field: 'waiver_warriors',
        map: (t) => ({ name: t.team_name, stat: `${t.pickup_count} pickups` }),
    },
    {
        key: 'draft_capital_movers', group: 'teams', category: 'Teams', icon: '↻',
        title: 'Commitment Issues',
        description: 'Teams that have traded away the most draft picks',
        source: 'teams', field: 'draft_capital_movers',
        map: (t) => ({ name: t.team_name, stat: `${t.picks_traded} picks` }),
    },
    // ── Draft ────────────────────────────────────────────────────
    {
        key: 'startup_loyalists', group: 'draft', category: 'Draft', icon: '★',
        title: "'Til Death Do Us Part",
        description: 'Players still on the team that drafted them in the startup',
        source: 'draft', field: 'startup_loyalists',
        map: (p) => ({ name: playerName(p), subtitle: p.team_name, stat: `R${p.round} · P${p.pick_no}` }),
    },
    {
        key: 'startup_steals', group: 'draft', category: 'Draft', icon: '↗',
        title: 'Out Of Their League',
        description: 'Latest startup picks still rostered in the league',
        source: 'draft', field: 'startup_steals',
        map: (p) => ({ name: playerName(p), subtitle: p.team_name, stat: `Pick ${p.pick_no}` }),
    },
    {
        key: 'rookie_draft_steals', group: 'draft', category: 'Draft', icon: '↺',
        title: 'Robbing The Cradle',
        description: 'Lowest rookie picks still on the team that drafted them',
        source: 'draft', field: 'rookie_draft_steals',
        map: (p) => ({ name: playerName(p), subtitle: p.team_name, stat: `'${p.season} R${p.round}` }),
    },
    // ── Scoring ──────────────────────────────────────────────────
    {
        key: 'nuke', group: 'scoring', category: 'Scoring', icon: '☄',
        title: 'Nuke',
        description: 'Highest single-week team score ever',
        source: 'scoring', field: 'nuke',
        map: (r) => ({ name: r.team_name, subtitle: `Wk ${r.week}, ${r.year} vs ${r.opponent_name}`, stat: `${r.points} pts` }),
    },
    {
        key: 'robbed', group: 'scoring', category: 'Scoring', icon: '⚐',
        title: 'Robbed',
        description: 'Most points ever scored in a loss',
        source: 'scoring', field: 'robbed',
        map: (r) => ({ name: r.team_name, subtitle: `Wk ${r.week}, ${r.year} · lost ${r.points}–${r.points_against}`, stat: `${r.points} pts` }),
    },
    {
        key: 'the_franchise', group: 'scoring', category: 'Scoring', icon: '★',
        title: 'The Franchise',
        description: 'Most career fantasy points across the league',
        source: 'scoring', field: 'the_franchise',
        map: (p) => ({ name: playerName(p), subtitle: p.position, stat: `${p.total_points} pts` }),
    },
    // ── Playoffs ─────────────────────────────────────────────────
    {
        key: 'frequent_flyer', group: 'playoffs', category: 'Playoffs', icon: '✈',
        title: 'Frequent Flyer',
        description: 'Most playoff appearances',
        source: 'playoffs', field: 'frequent_flyer',
        map: (t) => ({ name: t.team_name, subtitle: `${t.first_year}–${t.last_year}`, stat: `${t.appearances} apps` }),
    },
    {
        key: 'mr_january', group: 'playoffs', category: 'Playoffs', icon: '❄',
        title: 'Mr. January',
        description: 'Best playoff scoring average (min. 5 games)',
        source: 'playoffs', field: 'mr_january',
        map: (t) => ({ name: t.team_name, subtitle: `${t.games} playoff games`, stat: `${t.avg_points} ppg` }),
    },
    // ── Rivalries ────────────────────────────────────────────────
    {
        key: 'bad_blood', group: 'rivalries', category: 'Rivalries', icon: '⚔',
        title: 'Bad Blood',
        description: 'Most-played matchup, with the series record',
        source: 'rivalries', field: 'bad_blood',
        map: (r) => ({ name: `${r.team_1} vs ${r.team_2}`, subtitle: rivalryRecord(r), stat: `${r.meetings} mtgs` }),
    },
    {
        key: 'kryptonite', group: 'rivalries', category: 'Rivalries', icon: '☣',
        title: 'Kryptonite',
        description: "Each team's most frequent conqueror",
        source: 'rivalries', field: 'kryptonite',
        map: (r) => ({ name: r.team_name, subtitle: `owned by ${r.nemesis_name}`, stat: `${r.losses} L` }),
    },
    {
        key: 'free_square', group: 'rivalries', category: 'Rivalries', icon: '◎',
        title: 'Free Square',
        description: 'Team that has allowed the most points all-time',
        source: 'rivalries', field: 'free_square',
        map: (r) => ({ name: r.team_name, subtitle: `${r.games} games`, stat: `${r.points_allowed} pts` }),
    },
    // ── Starters ─────────────────────────────────────────────────
    {
        key: 'workhorse', group: 'starters', category: 'Starters', icon: '⚒',
        title: 'Workhorse',
        description: 'Most career points scored while starting',
        source: 'starters', field: 'workhorse',
        map: (p) => ({ name: playerName(p), subtitle: p.position, stat: `${p.total_points} pts` }),
    },
    {
        key: 'tenured', group: 'starters', category: 'Starters', icon: '⏱',
        title: 'Tenured',
        description: 'Most career starts (weeks in a starting lineup)',
        source: 'starters', field: 'tenured',
        map: (p) => ({ name: playerName(p), subtitle: p.position, stat: `${p.starts} starts` }),
    },
    {
        key: 'the_anchor', group: 'starters', category: 'Starters', icon: '⚓',
        title: 'The Anchor',
        description: 'Most starts, fewest points (min. 10 starts)',
        source: 'starters', field: 'the_anchor',
        map: (p) => ({ name: playerName(p), subtitle: `${p.starts} starts`, stat: `${p.avg_points} ppg` }),
    },
    {
        key: 'bench_warmers_revenge', group: 'starters', category: 'Starters', icon: '↩',
        title: "Bench Warmer's Revenge",
        description: 'Most career points scored while benched',
        source: 'starters', field: 'bench_warmers_revenge',
        map: (p) => ({ name: playerName(p), subtitle: `${p.games_benched} games benched`, stat: `${p.bench_points} pts` }),
    },
];

const FILTERS = [
    { key: 'all', label: 'All' },
    { key: 'players', label: 'Players' },
    { key: 'teams', label: 'Teams' },
    { key: 'draft', label: 'Draft' },
    { key: 'scoring', label: 'Scoring' },
    { key: 'playoffs', label: 'Playoffs' },
    { key: 'rivalries', label: 'Rivalries' },
    { key: 'starters', label: 'Starters' },
];

const SuperlativesArchive = () => {
    const [data, setData] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [filter, setFilter] = useState('all');
    const [page, setPage] = useState(1);

    useEffect(() => {
        const fetchOne = async (url) => {
            try {
                const res = await cachedFetch(url);
                if (!res.ok) return {};
                const json = await res.json();
                return json.superlatives || {};
            } catch {
                return {};
            }
        };

        const fetchAll = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);

                const [players, teams, draft, scoring, starters, rivalries, playoffs] = await Promise.all([
                    fetchOne(`${config.API_BASE_URL}/superlatives/players`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/teams`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/draft`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/scoring`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/starters`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/rivalries`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/playoffs`),
                ]);

                setData({ players, teams, draft, scoring, starters, rivalries, playoffs });
            } catch (error) {
                setFetchError(error.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchAll();
    }, []);

    const cards = useMemo(() => {
        if (!data) return [];
        return CATEGORIES
            .filter((c) => filter === 'all' || c.group === filter)
            .map((c) => {
                const raw = (data[c.source] || {})[c.field] || [];
                const rawByPos = PLAYER_KEYS.has(c.key)
                    ? (data[c.source] || {})[`${c.field}_by_position`]
                    : null;
                const byPosition = rawByPos
                    ? Object.fromEntries(
                        Object.entries(rawByPos).map(([pos, items]) => [pos, items.slice(0, 5).map(c.map)])
                    )
                    : null;
                return { ...c, entries: raw.slice(0, 5).map(c.map), byPosition };
            })
            .filter((c) => c.entries.length > 0);
    }, [data, filter]);

    const totalPages = Math.max(1, Math.ceil(cards.length / PER_PAGE));
    const currentPage = Math.min(page, totalPages);
    const pageItems = useMemo(() => {
        const start = (currentPage - 1) * PER_PAGE;
        return cards.slice(start, start + PER_PAGE);
    }, [cards, currentPage]);

    const handleFilter = (key) => { setFilter(key); setPage(1); };

    const renderBody = () => {
        if (isLoading) {
            return <div className="superlatives-archive-status">Loading superlatives...</div>;
        }
        if (fetchError) {
            return <div className="superlatives-archive-status superlatives-archive-error">Error loading superlatives: {fetchError}</div>;
        }
        if (cards.length === 0) {
            return (
                <div className="superlatives-archive-empty">
                    <span className="superlatives-archive-empty-icon">&#9734;</span>
                    <p>No superlatives in this category yet</p>
                </div>
            );
        }
        return (
            <>
                <div className="superlatives-archive-cards">
                    {pageItems.map((card) => (
                        <SuperlativeCard
                            key={card.key}
                            category={card.category}
                            icon={card.icon}
                            title={card.title}
                            tooltip={card.description}
                            entries={card.entries}
                            byPosition={card.byPosition}
                        />
                    ))}
                </div>
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={setPage}
                />
            </>
        );
    };

    return (
        <div className="superlatives-archive-page">
            <div className="superlatives-archive-header">
                <div className="superlatives-archive-title">
                    <span className="superlatives-archive-icon">&#9733;</span>
                    <h1>League Superlatives</h1>
                </div>
                {!isLoading && !fetchError && (
                    <span className="superlatives-archive-count">
                        {cards.length}<span className="superlatives-archive-count-sep"> / {CATEGORIES.length}</span> categories
                    </span>
                )}
            </div>

            <div className="superlatives-archive-filters">
                {FILTERS.map((f) => (
                    <button
                        key={f.key}
                        className={`superlatives-archive-pill${filter === f.key ? ' is-active' : ''}`}
                        onClick={() => handleFilter(f.key)}
                    >
                        {f.label}
                    </button>
                ))}
            </div>
            <div className="superlatives-archive-content">
                {renderBody()}
            </div>
        </div>
    );
};

export default SuperlativesArchive;
