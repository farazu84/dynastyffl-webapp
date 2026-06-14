import React, { useState, useEffect } from 'react';
import TeamItem from '../league/TeamItem';
import ChampionModal from './ChampionModal';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/League.css';
import '../../styles/AllTimeRecords.css';

const RecentChampions = () => {
    const [champions, setChampions] = useState(null);
    const [selectedYear, setSelectedYear] = useState(null);

    useEffect(() => {
        const fetchChampions = async () => {
            try {
                const res = await cachedFetch(`${config.API_BASE_URL}/teams/recent_champions`);
                if (!res.ok) return;
                const json = await res.json();
                setChampions(json.champions || []);
            } catch {
                setChampions([]);
            }
        };

        fetchChampions();
    }, []);

    if (!champions || champions.length === 0) return null;

    return (
        <section className="recent-champions-section">
            <div className="recent-champions-header">
                <h2>Recent Champions</h2>
            </div>
            <ul className="teamList">
                {champions.map((champion) => (
                    <TeamItem
                        key={champion.year}
                        team={champion}
                        record={champion.season_record}
                        badge={champion.year}
                        onSelect={() => setSelectedYear(champion.year)}
                    />
                ))}
            </ul>
            {selectedYear != null && (
                <ChampionModal year={selectedYear} onClose={() => setSelectedYear(null)} />
            )}
        </section>
    );
};

export default RecentChampions;
