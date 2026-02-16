import React, { useState, useEffect, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import config from '../../config';
import { cachedFetch } from '../../utils/apiCache';
import OriginCard from '../../components/trade-tree/OriginCard';
import TeamBranch from '../../components/trade-tree/TeamBranch';
import '../../styles/TradeTree.css';

const TradeTree = React.memo(() => {
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
            <Link to="/archive" className="trade-tree-back">
                ← Back to Archive
            </Link>
            <OriginCard origin={treeData.origin} />
            <div className="trade-tree-branches">
                {teamBranches}
            </div>
        </main>
    );
});

TradeTree.displayName = 'TradeTree';

export default TradeTree;
