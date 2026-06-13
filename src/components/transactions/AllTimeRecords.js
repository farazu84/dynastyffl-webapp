import React, { useState, useEffect } from 'react';
import TeamItem from '../league/TeamItem';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/League.css';
import '../../styles/AllTimeRecords.css';

const AllTimeRecords = () => {
    const [teams, setTeams] = useState(null);

    useEffect(() => {
        const fetchAllTime = async () => {
            try {
                const res = await cachedFetch(`${config.API_BASE_URL}/teams/all_time`);
                if (!res.ok) return;
                const json = await res.json();
                setTeams(json.teams || []);
            } catch {
                setTeams([]);
            }
        };

        fetchAllTime();
    }, []);

    if (!teams || teams.length === 0) return null;

    const splitIndex = Math.ceil(teams.length / 2);
    const left = teams.slice(0, splitIndex);
    const right = teams.slice(splitIndex);

    return (
        <section className="all-time-records-section">
            <div className="all-time-records-header">
                <h2>All-Time Records</h2>
            </div>
            <div className="all-time-records-columns">
                <ul className="teamList">
                    {left.map((team, i) => (
                        <TeamItem
                            key={team.team_id}
                            team={team}
                            record={team.all_time_record}
                            rank={i + 1}
                        />
                    ))}
                </ul>
                <ul className="teamList">
                    {right.map((team, i) => (
                        <TeamItem
                            key={team.team_id}
                            team={team}
                            record={team.all_time_record}
                            rank={left.length + i + 1}
                        />
                    ))}
                </ul>
            </div>
        </section>
    );
};

export default AllTimeRecords;
