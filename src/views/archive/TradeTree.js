import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import { formatDate } from '../../utils/formatters';
import OriginCard from '../../components/trade-tree/OriginCard';
import TeamBranch from '../../components/trade-tree/TeamBranch';
import '../../styles/TradeTree.css';

const TradeTree = () => {
    const { transactionId } = useParams();
    const [treeData, setTreeData] = useState(null);
    const [fetchError, setFetchError] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        const fetchTree = async () => {
            try {
                setIsLoading(true);
                setFetchError(null);
                const response = await cachedFetch(
                    `${config.API_BASE_URL}/transactions/${transactionId}/full_trade_tree`
                );
                if (!response.ok) throw new Error(`API error: ${response.status}`);
                const data = await response.json();
                if (!data.success) throw new Error(data.error || 'Failed to load trade tree');
                setTreeData(data);
            } catch (error) {
                console.error('Trade tree fetch error:', error);
                setFetchError(error.message);
            } finally {
                setIsLoading(false);
            }
        };

        if (transactionId) fetchTree();
    }, [transactionId]);

    const teamBranches = useMemo(() => {
        if (!treeData?.teams) return [];
        return Object.entries(treeData.teams).map(([rosterId, teamData]) => (
            <TeamBranch
                key={rosterId}
                team={teamData}
                pickMetadata={treeData.pick_metadata || {}}
                originDate={treeData.origin.created_at}
            />
        ));
    }, [treeData]);

    const teamNames = useMemo(() => {
        if (!treeData?.origin?.roster_moves) return '';
        const names = [...new Set(
            treeData.origin.roster_moves.map(rm => rm.team?.team_name).filter(Boolean)
        )];
        return names.join(' & ');
    }, [treeData]);

    if (isLoading) {
        return (
            <main className="trade-tree-page">
                <div className="trade-tree-loading">Loading trade tree...</div>
            </main>
        );
    }

    if (fetchError) {
        return (
            <main className="trade-tree-page">
                <div className="trade-tree-error">Error loading trade tree: {fetchError}</div>
            </main>
        );
    }

    return (
        <main className="trade-tree-page">
            <div className="trade-tree-header">
                <h1 className="trade-tree-title">Trade Tree</h1>
                <p className="trade-tree-subtitle">{teamNames} — {formatDate(treeData.origin.created_at)}</p>
            </div>
            <OriginCard origin={treeData.origin} />
            <div className="trade-tree-branches">
                {teamBranches}
            </div>
        </main>
    );
};

export default TradeTree;
