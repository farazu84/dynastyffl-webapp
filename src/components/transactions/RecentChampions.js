import React, { useState, useEffect } from 'react';
import TeamItem from '../league/TeamItem';
import ChampionModal from './ChampionModal';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/League.css';
import '../../styles/AllTimeRecords.css';

const PAGE_SIZE = 5;

const RecentChampions = () => {
    const [champions, setChampions] = useState(null);
    const [selectedYear, setSelectedYear] = useState(null);
    const [page, setPage] = useState(0);

    useEffect(() => {
        const fetchChampions = async () => {
            try {
                const res = await cachedFetch(`${config.API_BASE_URL}/teams/recent_champions`);
                if (!res.ok) return;
                const json = await res.json();
                setChampions(json.champions || []);
                setPage(0);
            } catch {
                setChampions([]);
            }
        };

        fetchChampions();
    }, []);

    if (!champions || champions.length === 0) return null;

    const totalPages = Math.ceil(champions.length / PAGE_SIZE);
    const visibleChampions = champions.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
    const newestYear = visibleChampions[0].year;
    const oldestYear = visibleChampions[visibleChampions.length - 1].year;
    const yearLabel = newestYear === oldestYear ? `${newestYear}` : `${oldestYear} – ${newestYear}`;

    return (
        <section className="recent-champions-section">
            <div className="recent-champions-header">
                <h2>Champions</h2>
            </div>
            <ul className="teamList">
                {visibleChampions.map((champion) => (
                    <TeamItem
                        key={champion.year}
                        team={champion}
                        record={champion.season_record}
                        badge={champion.year}
                        onSelect={() => setSelectedYear(champion.year)}
                    />
                ))}
            </ul>
            {totalPages > 1 && (
                <div className="champions-pagination">
                    <button
                        onClick={() => setPage(p => p - 1)}
                        disabled={page === 0}
                        aria-label="Newer champions"
                    >
                        ←
                    </button>
                    <span className="year-range">{yearLabel}</span>
                    <button
                        onClick={() => setPage(p => p + 1)}
                        disabled={page >= totalPages - 1}
                        aria-label="Older champions"
                    >
                        →
                    </button>
                </div>
            )}
            {selectedYear != null && (
                <ChampionModal year={selectedYear} onClose={() => setSelectedYear(null)} />
            )}
        </section>
    );
};

export default RecentChampions;
