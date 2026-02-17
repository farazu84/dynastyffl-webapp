import React from 'react';

const SuperlativeCard = ({ icon, title, tooltip, entries }) => {
    return (
        <div className="superlative-card">
            <div className="superlative-card-icon">{icon}</div>
            <div className="superlative-card-title-row">
                <div className="superlative-card-title">{title}</div>
                {tooltip && <span className="superlative-card-tooltip" data-tip={tooltip} tabIndex={0} role="img" aria-label={tooltip}>!</span>}
            </div>
            <div className="superlative-card-list">
                {entries.map((entry, idx) => (
                    <div className={`superlative-card-entry${idx === 0 ? ' superlative-card-entry-top' : ''}`} key={idx}>
                        <div className="superlative-entry-name-col">
                            <span className="superlative-entry-name">{entry.name}</span>
                            {entry.subtitle && <span className="superlative-entry-subtitle">{entry.subtitle}</span>}
                        </div>
                        <span className="superlative-entry-stat">{entry.stat}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default React.memo(SuperlativeCard);
