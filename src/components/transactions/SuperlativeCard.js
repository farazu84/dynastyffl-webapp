import React, { useState } from 'react';

const POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K'];

const SuperlativeCard = ({ category, icon, title, tooltip, entries, byPosition }) => {
    const [posFilter, setPosFilter] = useState('all');

    const displayed = (byPosition && posFilter !== 'all')
        ? (byPosition[posFilter] || [])
        : entries;

    return (
        <div className="superlative-card">
            <div className="superlative-card-top">
                {category && <span className="superlative-card-tag">{category}</span>}
                {icon && <span className="superlative-card-icon">{icon}</span>}
            </div>
            <h3 className="superlative-card-title">{title}</h3>
            {tooltip && <p className="superlative-card-desc">{tooltip}</p>}
            {byPosition && (
                <div className="superlative-card-pos-filters">
                    <button
                        className={`superlative-card-pos-pill${posFilter === 'all' ? ' is-active' : ''}`}
                        onClick={() => setPosFilter('all')}
                    >
                        All
                    </button>
                    {POSITIONS.map((pos) => (
                        <button
                            key={pos}
                            className={`superlative-card-pos-pill${posFilter === pos ? ' is-active' : ''}`}
                            onClick={() => setPosFilter(pos)}
                        >
                            {pos}
                        </button>
                    ))}
                </div>
            )}
            <div className="superlative-card-list">
                {displayed.length > 0 ? displayed.map((entry, idx) => (
                    <div className={`superlative-card-entry${idx === 0 ? ' superlative-card-entry-top' : ''}`} key={idx}>
                        <span className="superlative-entry-rank">#{idx + 1}</span>
                        <div className="superlative-entry-name-col">
                            <span className="superlative-entry-name">{entry.name}</span>
                            {entry.subtitle && <span className="superlative-entry-subtitle">{entry.subtitle}</span>}
                        </div>
                        <span className="superlative-entry-stat">{entry.stat}</span>
                    </div>
                )) : (
                    <div className="superlative-card-empty-pos">No {posFilter} data</div>
                )}
            </div>
        </div>
    );
};

export default React.memo(SuperlativeCard);
