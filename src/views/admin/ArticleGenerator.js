import React, { useState, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useAuthFetch } from '../../hooks/useAuthFetch';

const ARTICLE_TYPES = [
    { value: 'power_ranking', label: 'Power Rankings' },
    { value: 'franchise_ranking', label: 'Franchise Rankings' },
    { value: 'pregame_report', label: 'Pregame Report' },
    { value: 'rumor', label: 'Rumor' },
    { value: 'weekly_recap', label: 'Weekly Recap' },
    { value: 'team_analysis', label: 'Team Analysis' },
];

const WEEKS = Array.from({ length: 17 }, (_, i) => i + 1);

const ArticleGenerator = ({ onGenerated }) => {
    const authFetch = useAuthFetch();

    const [articleType, setArticleType] = useState('power_ranking');
    const [teams, setTeams] = useState([]);
    const [matchups, setMatchups] = useState([]);

    const [selectedMatchupId, setSelectedMatchupId] = useState('');
    const [selectedTeamIds, setSelectedTeamIds] = useState([]);
    const [selectedTeamId, setSelectedTeamId] = useState('');
    const [rumorText, setRumorText] = useState('');
    const [week, setWeek] = useState('');

    const [generating, setGenerating] = useState(false);
    const [genError, setGenError] = useState(null);
    const [generatedArticle, setGeneratedArticle] = useState(null);
    const [publishing, setPublishing] = useState(false);
    const [publishError, setPublishError] = useState(null);

    useEffect(() => {
        const fetchTeams = async () => {
            try {
                const res = await authFetch('/teams');
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                const data = await res.json();
                setTeams(data.teams || []);
            } catch (err) {
                setGenError(err.message);
            }
        };
        fetchTeams();
    }, [authFetch]);

    useEffect(() => {
        const fetchMatchups = async () => {
            try {
                const res = await authFetch('/matchups/current_matchups');
                if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
                const data = await res.json();
                setMatchups(data.matchups || []);
                if (data.matchups?.length) setWeek(String(data.matchups[0].week));
            } catch (err) {
                setGenError(err.message);
            }
        };
        fetchMatchups();
    }, [authFetch]);

    const handleTeamToggle = useCallback((teamId) => {
        setSelectedTeamIds(prev =>
            prev.includes(teamId)
                ? prev.filter(id => id !== teamId)
                : [...prev, teamId]
        );
    }, []);

    const isValid = (() => {
        switch (articleType) {
            case 'pregame_report': return !!selectedMatchupId;
            case 'rumor': return rumorText.trim() && selectedTeamIds.length > 0;
            case 'weekly_recap': return !!week;
            case 'team_analysis': return !!selectedTeamId;
            default: return true;
        }
    })();

    const handleGenerate = useCallback(async () => {
        setGenerating(true);
        setGenError(null);
        setPublishError(null);
        setGeneratedArticle(null);
        try {
            let body = {};
            if (articleType === 'pregame_report') {
                const matchup = matchups.find(m => String(m.sleeper_matchup_id) === selectedMatchupId);
                body = { sleeper_matchup_id: matchup.sleeper_matchup_id, week: matchup.week };
            } else if (articleType === 'rumor') {
                body = { rumor: rumorText, team_ids: selectedTeamIds };
            } else if (articleType === 'weekly_recap') {
                body = { week: parseInt(week, 10) };
            } else if (articleType === 'team_analysis') {
                body = { team_id: parseInt(selectedTeamId, 10) };
            }

            const res = await authFetch(`/admin/articles/generate/${articleType}`, {
                method: 'POST',
                body: JSON.stringify(body),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to generate article');
            setGeneratedArticle(data.article);
            onGenerated?.();
        } catch (err) {
            setGenError(err.message);
        } finally {
            setGenerating(false);
        }
    }, [articleType, matchups, selectedMatchupId, rumorText, selectedTeamIds, week, selectedTeamId, authFetch, onGenerated]);

    const handlePublish = useCallback(async () => {
        if (!generatedArticle) return;
        setPublishing(true);
        setPublishError(null);
        try {
            const res = await authFetch(`/admin/articles/${generatedArticle.article_id}/publish`, { method: 'POST' });
            const data = await res.json();
            if (!res.ok) throw new Error(data.error || 'Failed to publish article');
            setGeneratedArticle(data.article);
            onGenerated?.();
        } catch (err) {
            setPublishError(err.message);
        } finally {
            setPublishing(false);
        }
    }, [generatedArticle, authFetch, onGenerated]);

    return (
        <section className="admin-section">
            <h2 className="admin-section-title">AI Articles</h2>

            <div className="admin-udfa-block">
                <div className="admin-articlegen-row">
                    <div className="admin-datepicker-wrap">
                        <label className="admin-datepicker-label">Article Type</label>
                        <select
                            className="admin-select"
                            value={articleType}
                            onChange={e => setArticleType(e.target.value)}
                        >
                            {ARTICLE_TYPES.map(t => (
                                <option key={t.value} value={t.value}>{t.label}</option>
                            ))}
                        </select>
                    </div>

                    {articleType === 'pregame_report' && (
                        <div className="admin-datepicker-wrap">
                            <label className="admin-datepicker-label">Matchup</label>
                            <select
                                className="admin-select"
                                value={selectedMatchupId}
                                onChange={e => setSelectedMatchupId(e.target.value)}
                            >
                                <option value="">Select a matchup...</option>
                                {matchups.map(m => (
                                    <option key={m.matchup_id} value={m.sleeper_matchup_id}>
                                        {m.team?.team_name} vs {m.opponent_team?.team_name} (Week {m.week})
                                    </option>
                                ))}
                            </select>
                        </div>
                    )}

                    {articleType === 'weekly_recap' && (
                        <div className="admin-datepicker-wrap">
                            <label className="admin-datepicker-label">Week</label>
                            <select
                                className="admin-select"
                                value={week}
                                onChange={e => setWeek(e.target.value)}
                            >
                                {WEEKS.map(w => (
                                    <option key={w} value={w}>Week {w}</option>
                                ))}
                            </select>
                        </div>
                    )}

                    {articleType === 'team_analysis' && (
                        <div className="admin-datepicker-wrap">
                            <label className="admin-datepicker-label">Team</label>
                            <select
                                className="admin-select"
                                value={selectedTeamId}
                                onChange={e => setSelectedTeamId(e.target.value)}
                            >
                                <option value="">Select a team...</option>
                                {teams.map(t => (
                                    <option key={t.team_id} value={t.team_id}>{t.team_name}</option>
                                ))}
                            </select>
                        </div>
                    )}
                </div>

                {articleType === 'power_ranking' && (
                    <p className="admin-udfa-block-desc">Ranks all teams by current-season performance: records, points, and recent results. References the last published power rankings for movement.</p>
                )}

                {articleType === 'franchise_ranking' && (
                    <p className="admin-udfa-block-desc">Ranks all teams by long-term dynasty value: young assets, win-now talent, and competitive windows. References the last published franchise rankings for movement.</p>
                )}

                {articleType === 'rumor' && (
                    <>
                        <div className="admin-articlegen-teamlist">
                            {teams.map(t => (
                                <label key={t.team_id} className="admin-articlegen-teamcheck">
                                    <input
                                        type="checkbox"
                                        checked={selectedTeamIds.includes(t.team_id)}
                                        onChange={() => handleTeamToggle(t.team_id)}
                                    />
                                    <span>{t.team_name}</span>
                                </label>
                            ))}
                        </div>
                        <textarea
                            className="admin-articlegen-textarea"
                            value={rumorText}
                            onChange={e => setRumorText(e.target.value)}
                            placeholder="What's the rumor? Be specific about the players and teams involved."
                            rows={4}
                            maxLength={500}
                        />
                    </>
                )}

                <div className="admin-udfa-row">
                    <button
                        className="admin-action-btn"
                        onClick={handleGenerate}
                        disabled={generating || !isValid}
                    >
                        {generating ? (
                            <>
                                <span className="admin-spinner" />
                                Generating… (this can take a minute)
                            </>
                        ) : 'Generate Article'}
                    </button>
                </div>

                {genError && <p className="admin-error">{genError}</p>}

                {generatedArticle && (
                    <div className="admin-article-preview">
                        <div className="admin-article-preview-header">
                            <div>
                                <h3 className="admin-article-preview-title">{generatedArticle.title}</h3>
                                <span className="admin-article-preview-author">by {generatedArticle.author}</span>
                            </div>
                            <div className="admin-article-preview-actions">
                                <span className={`admin-article-preview-badge ${generatedArticle.published ? 'admin-article-preview-badge--published' : ''}`}>
                                    {generatedArticle.published ? 'Published' : 'Draft'}
                                </span>
                                {!generatedArticle.published && (
                                    <button
                                        className="admin-action-btn"
                                        onClick={handlePublish}
                                        disabled={publishing}
                                    >
                                        {publishing ? 'Publishing...' : 'Publish'}
                                    </button>
                                )}
                            </div>
                        </div>
                        {publishError && <p className="admin-error">{publishError}</p>}
                        <div className="admin-article-preview-content">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                {generatedArticle.content}
                            </ReactMarkdown>
                        </div>
                    </div>
                )}
            </div>
        </section>
    );
};

export default ArticleGenerator;
