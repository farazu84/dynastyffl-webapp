import { useState, useEffect } from 'react';
import '../../styles/Rumor.css';

const Rumor = () => {
    const [rumorText, setRumorText] = useState('');
    const [teams, setTeams] = useState([]);
    const [selectedTeams, setSelectedTeams] = useState([]);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [submitMessage, setSubmitMessage] = useState('');

    // Fetch teams for the dropdown
    useEffect(() => {
        const fetchTeams = async () => {
            try {
                const response = await fetch('/teams');
                const data = await response.json();
                setTeams(data.teams || []);
            } catch (error) {
                console.error('Error fetching teams:', error);
            }
        };
        fetchTeams();
    }, []);

    const handleTeamToggle = (teamId) => {
        setSelectedTeams(prev => 
            prev.includes(teamId) 
                ? prev.filter(id => id !== teamId)
                : [...prev, teamId]
        );
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!rumorText.trim()) {
            setSubmitMessage('Please enter a rumor before submitting.');
            return;
        }

        setIsSubmitting(true);
        setSubmitMessage('');

        try {
            const response = await fetch('/articles/generate_rumor', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    rumor: rumorText,
                    team_ids: selectedTeams
                })
            });

            if (response.ok) {
                setSubmitMessage('Rumor submitted successfully!');
                setRumorText('');
                setSelectedTeams([]);
            } else {
                setSubmitMessage('Failed to submit rumor. Please try again.');
            }
        } catch (error) {
            console.error('Error submitting rumor:', error);
            setSubmitMessage('Error submitting rumor. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="rumor-page">
            <div className="rumor-container">
                <h1 className="rumor-title">Rumor Mill</h1>
                <p className="rumor-subtitle">
                    All rumors are anonymous!
                </p>

                <form onSubmit={handleSubmit} className="rumor-form">
                    <div className="form-group">
                        <textarea
                            id="rumor-text"
                            value={rumorText}
                            onChange={(e) => setRumorText(e.target.value)}
                            placeholder="Please be specific about the players and teams involved, this will be fed to an AI to generate an article."
                            className="rumor-textarea"
                            rows={6}
                            maxLength={500}
                        />
                        <div className="character-count">
                            {rumorText.length}/500 characters
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">
                            Tag Teams
                        </label>
                        <p className="form-helper">
                            Select all teams involved in rumor.
                        </p>
                        <div className="teams-dropdown">
                            {teams.map(team => (
                                <label key={team.team_id} className="team-checkbox">
                                    <input
                                        type="checkbox"
                                        checked={selectedTeams.includes(team.team_id)}
                                        onChange={() => handleTeamToggle(team.team_id)}
                                        className="checkbox-input"
                                    />
                                    <span className="checkbox-custom"></span>
                                    <span className="team-name">{team.team_name}</span>
                                </label>
                            ))}
                        </div>
                        
                        {selectedTeams.length > 0 && (
                            <div className="selected-teams">
                                <span className="selected-label">Selected: </span>
                                {selectedTeams.map(teamId => {
                                    const team = teams.find(t => t.team_id === teamId);
                                    return team ? (
                                        <span key={teamId} className="selected-team-tag">
                                            {team.team_name}
                                            <button 
                                                type="button"
                                                onClick={() => handleTeamToggle(teamId)}
                                                className="remove-tag"
                                            >
                                                ×
                                            </button>
                                        </span>
                                    ) : null;
                                })}
                            </div>
                        )}
                    </div>

                    <button 
                        type="submit" 
                        disabled={isSubmitting || !rumorText.trim()}
                        className="submit-btn"
                    >
                        {isSubmitting ? 'Submitting...' : 'Spread Rumor'}
                    </button>
                </form>

                {submitMessage && (
                    <div className={`submit-message ${submitMessage.includes('successfully') ? 'success' : 'error'}`}>
                        {submitMessage}
                    </div>
                )}
            </div>
        </div>
    )
}

export default Rumor;