import { useState, useMemo, useEffect } from 'react';
import PlayerRow from './PlayerRow';
import Pagination from '../shared/Pagination';

const PAGE_SIZE = 10;
const POSITION_ORDER = ['QB', 'RB', 'WR', 'TE', 'K'];

const HeaderFilter = ({ value, onChange, label, className, children }) => (
    <div className={`udfa-header-filter ${className} ${value ? 'active' : ''}`}>
        <span className="udfa-header-filter-text">{value || label}</span>
        <span className="udfa-header-filter-caret">▾</span>
        <select
            className="udfa-header-select-hidden"
            value={value}
            onChange={e => onChange(e.target.value)}
        >
            {children}
        </select>
    </div>
);

const TableHeader = ({ showFilters, positions, nflTeams, positionFilter, setPositionFilter, nflTeamFilter, setNflTeamFilter }) => (
    <div className="player-row-item player-table-header">
        {showFilters ? (
            <HeaderFilter value={positionFilter} onChange={setPositionFilter} label="POS" className="position-filter">
                <option value="">POS</option>
                {positions.map(pos => <option key={pos} value={pos}>{pos}</option>)}
            </HeaderFilter>
        ) : (
            <span className="player-table-header-static">POS</span>
        )}
        <span>PLAYER</span>
        {showFilters ? (
            <HeaderFilter value={nflTeamFilter} onChange={setNflTeamFilter} label="NFL TEAM" className="nfl-team-filter">
                <option value="">NFL TEAM</option>
                {nflTeams.map(team => <option key={team} value={team}>{team}</option>)}
            </HeaderFilter>
        ) : (
            <span className="player-table-header-static nfl-team-static">NFL TEAM</span>
        )}
        <span>BID STATUS</span>
    </div>
);

const PlayerTable = ({ title, players, showFilters = true, onPlaceBid, onEditBid, onRetractBid }) => {
    const [positionFilter, setPositionFilter] = useState('');
    const [nflTeamFilter, setNflTeamFilter] = useState('');
    const [currentPage, setCurrentPage] = useState(1);

    const positions = useMemo(() => {
        const unique = new Set(players.map(p => p.position).filter(Boolean));
        return POSITION_ORDER.filter(pos => unique.has(pos));
    }, [players]);

    const nflTeams = useMemo(() => {
        const unique = [...new Set(players.map(p => p.nfl_team).filter(Boolean))];
        return unique.sort();
    }, [players]);

    const filteredPlayers = useMemo(() => {
        if (!showFilters) return players;
        return players.filter(p => {
            if (positionFilter && p.position !== positionFilter) return false;
            if (nflTeamFilter && p.nfl_team !== nflTeamFilter) return false;
            return true;
        });
    }, [players, positionFilter, nflTeamFilter, showFilters]);

    useEffect(() => { setCurrentPage(1); }, [positionFilter, nflTeamFilter]);

    const totalPages = showFilters ? Math.ceil(filteredPlayers.length / PAGE_SIZE) : 1;
    const visiblePlayers = showFilters
        ? filteredPlayers.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)
        : filteredPlayers;

    if (!showFilters && players.length === 0) return null;

    return (
        <div className="player-table">
            {title && <h3 className="player-table-title">{title}</h3>}
            <TableHeader
                showFilters={showFilters}
                positions={positions}
                nflTeams={nflTeams}
                positionFilter={positionFilter}
                setPositionFilter={setPositionFilter}
                nflTeamFilter={nflTeamFilter}
                setNflTeamFilter={setNflTeamFilter}
            />
            <div className="player-table-body">
                {filteredPlayers.length === 0 ? (
                    <p className="udfa-status">No players match the selected filters.</p>
                ) : (
                    visiblePlayers.map(player => (
                        <PlayerRow
                            key={player.sleeper_id}
                            player={player}
                            onPlaceBid={onPlaceBid}
                            onEditBid={onEditBid}
                            onRetractBid={onRetractBid}
                        />
                    ))
                )}
            </div>
            {showFilters && (
                <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    onPageChange={setCurrentPage}
                />
            )}
        </div>
    );
};

export default PlayerTable;
