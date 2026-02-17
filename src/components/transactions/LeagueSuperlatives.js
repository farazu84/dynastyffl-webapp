import React, { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import SuperlativeCard from './SuperlativeCard';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import '../../styles/LeagueSuperlatives.css';

const LeagueSuperlatives = () => {
    const [playerData, setPlayerData] = useState(null);
    const [teamData, setTeamData] = useState(null);
    const [draftData, setDraftData] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

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

        const fetchSuperlatives = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);

                const [player, team, draft] = await Promise.all([
                    fetchOne(`${config.API_BASE_URL}/superlatives/players`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/teams`),
                    fetchOne(`${config.API_BASE_URL}/superlatives/draft`),
                ]);

                setPlayerData(player);
                setTeamData(team);
                setDraftData(draft);
            } catch (error) {
                setFetchError(error.message);
            } finally {
                setIsLoading(false);
            }
        };

        fetchSuperlatives();
    }, []);

    const cards = useMemo(() => {
        if (!playerData || !teamData || !draftData) return [];

        return [
            {
                icon: '\u21BA',
                title: "Should I Call My Ex?",
                tooltip: 'Players re-added to the same team the most times',
                entries: (playerData.boomerang || []).slice(0, 5).map((p) => ({
                    name: `${p.first_name} ${p.last_name}`,
                    subtitle: p.team_name,
                    stat: `${p.times_added}x`,
                })),
            },
            {
                icon: '\u2197',
                title: 'Ghosted',
                tooltip: 'Players dropped the most times across the league',
                entries: (playerData.most_dropped || []).slice(0, 5).map((p) => ({
                    name: `${p.first_name} ${p.last_name}`,
                    stat: `${p.drop_count} Drops`,
                })),
            },
            {
                icon: '\u21BB',
                title: 'Making The Rounds',
                tooltip: 'Players rostered by the most different teams',
                entries: (playerData.most_teams || []).slice(0, 5).map((p) => ({
                    name: `${p.first_name} ${p.last_name}`,
                    stat: `${p.team_count} Teams`,
                })),
            },
            {
                icon: '\u21C4',
                title: 'Eskimo Brothers',
                tooltip: 'Team pairs that have traded with each other the most',
                entries: (teamData.frequent_trade_partners || []).slice(0, 5).map((p) => ({
                    name: `${p.team_1} + ${p.team_2}`,
                    stat: `${p.trade_count} Trades`,
                })),
            },
            {
                icon: '\u2605',
                title: "'Til Death Do Us Part",
                tooltip: 'Players still on the team that drafted them in the startup',
                entries: (draftData.startup_loyalists || []).slice(0, 5).map((p) => ({
                    name: `${p.first_name} ${p.last_name}`,
                    subtitle: p.team_name,
                    stat: `2019-${new Date().getFullYear()}`,
                })),
            },
        ];
    }, [playerData, teamData, draftData]);

    if (isLoading) {
        return (
            <section className="league-superlatives-section">
                <div className="league-superlatives-header">
                    <span className="league-superlatives-icon">&#9734;</span>
                    <h2>League Superlatives</h2>
                </div>
                <div className="league-superlatives-loading">Loading superlatives...</div>
            </section>
        );
    }

    if (fetchError) {
        return (
            <section className="league-superlatives-section">
                <div className="league-superlatives-header">
                    <span className="league-superlatives-icon">&#9734;</span>
                    <h2>League Superlatives</h2>
                </div>
                <div className="league-superlatives-error">Error loading superlatives: {fetchError}</div>
            </section>
        );
    }

    return (
        <section className="league-superlatives-section">
            <div className="league-superlatives-header">
                <div className="league-superlatives-title">
                    <span className="league-superlatives-icon">&#9734;</span>
                    <h2>League Superlatives</h2>
                </div>
                <Link to="/archive" className="league-superlatives-view-all">
                    View All
                </Link>
            </div>
            <div className="league-superlatives-cards">
                {cards.map((card) => (
                    <SuperlativeCard
                        key={card.title}
                        icon={card.icon}
                        title={card.title}
                        tooltip={card.tooltip}
                        entries={card.entries}
                    />
                ))}
            </div>
        </section>
    );
};

export default LeagueSuperlatives;
