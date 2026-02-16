import React, { useState, useEffect, useMemo } from 'react';
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
        const fetchSuperlatives = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);

                const [playerRes, teamRes, draftRes] = await Promise.all([
                    cachedFetch(`${config.API_BASE_URL}/superlatives/players`),
                    cachedFetch(`${config.API_BASE_URL}/superlatives/teams`),
                    cachedFetch(`${config.API_BASE_URL}/superlatives/draft`),
                ]);

                if (!playerRes.ok) throw new Error(`Player superlatives error: ${playerRes.status}`);
                if (!teamRes.ok) throw new Error(`Team superlatives error: ${teamRes.status}`);
                if (!draftRes.ok) throw new Error(`Draft superlatives error: ${draftRes.status}`);

                const [playerJson, teamJson, draftJson] = await Promise.all([
                    playerRes.json(),
                    teamRes.json(),
                    draftRes.json(),
                ]);

                setPlayerData(playerJson.superlatives || {});
                setTeamData(teamJson.superlatives || {});
                setDraftData(draftJson.superlatives || {});
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

        const currentYear = new Date().getFullYear();

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
                    stat: '2019-Current',
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
                <button className="league-superlatives-view-all" onClick={() => window.location.href = '/archive'}>
                    View All
                </button>
            </div>
            <div className="league-superlatives-cards">
                {cards.map((card, idx) => (
                    <SuperlativeCard
                        key={idx}
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
