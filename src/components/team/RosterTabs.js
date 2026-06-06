import React, { useState } from 'react';
import RosterRow, { computeSlots } from './RosterRow';

const TABS = [
    { key: 'lineup', label: 'Lineup' },
    { key: 'bench',  label: 'Bench'  },
    { key: 'taxi',   label: 'Taxi'   },
];

const RosterTabs = ({ starters, bench, taxi }) => {
    const [activeTab, setActiveTab] = useState('lineup');

    const playersByTab = { lineup: starters, bench, taxi };
    const players = playersByTab[activeTab] ?? [];

    const slots = activeTab === 'lineup'
        ? computeSlots(starters)
        : players.map(p => p.position);

    return (
        <div className="roster-tabs">
            {/* Tab bar */}
            <div className="roster-tab-bar">
                {TABS.map(({ key, label }) => (
                    <button
                        key={key}
                        className={`roster-tab${activeTab === key ? ' roster-tab--active' : ''}`}
                        onClick={() => setActiveTab(key)}
                    >
                        {label}
                        <span className="roster-tab-count">
                            {playersByTab[key]?.length ?? 0}
                        </span>
                    </button>
                ))}
            </div>

            {/* Table */}
            <div className="roster-table">
                {/* Header */}
                <div className="roster-table-header">
                    <span>Slot</span>
                    <span className="roster-col-player">Player</span>
                    <span>NFL</span>
                    <span>Age</span>
                    <span>Exp</span>
                    <span className="roster-col-status">Status</span>
                </div>

                {/* Rows */}
                {players.length > 0 ? (
                    players.map((player, i) => (
                        <RosterRow
                            key={player.player_id}
                            player={player}
                            slot={slots[i]}
                        />
                    ))
                ) : (
                    <div style={{
                        gridColumn: '1 / -1',
                        padding: '24px',
                        textAlign: 'center',
                        fontFamily: 'var(--mono)',
                        fontSize: '0.7rem',
                        letterSpacing: '.1em',
                        textTransform: 'uppercase',
                        color: 'var(--muted)',
                        borderBottom: '1px solid var(--stroke)',
                    }}>
                        No players
                    </div>
                )}
            </div>
        </div>
    );
};

export default RosterTabs;
