-- Migration: Add simulation tables for AI agent ensemble matchup predictions

CREATE TABLE MatchupSimulations (
    simulation_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    matchup_id INT NOT NULL,
    week INT NOT NULL,
    year INT NOT NULL,
    team_a_win_probability FLOAT NOT NULL,
    team_a_median_score FLOAT NOT NULL,
    team_b_median_score FLOAT NOT NULL,
    -- IQR of agent predictions — high value signals a contested/upset-prone matchup
    team_a_score_spread FLOAT NOT NULL,
    team_b_score_spread FLOAT NOT NULL,
    -- Full raw audit trail of all agent responses
    agent_results JSON NOT NULL,
    n_agents INT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (simulation_id),
    FOREIGN KEY (matchup_id) REFERENCES Matchups(matchup_id),
    INDEX ix_simulations_matchup_week (matchup_id, week)
);

-- One row per player × per persona × per simulation
-- Enables historical accuracy analysis: which persona best predicted which position?
CREATE TABLE SimulationPlayerProjections (
    projection_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    simulation_id INT UNSIGNED NOT NULL,
    player_id INT NOT NULL,
    persona VARCHAR(64) NOT NULL,
    projected_score FLOAT NOT NULL,
    reasoning TEXT NULL,
    PRIMARY KEY (projection_id),
    FOREIGN KEY (simulation_id) REFERENCES MatchupSimulations(simulation_id),
    FOREIGN KEY (player_id) REFERENCES Players(player_id),
    INDEX ix_sim_player_projections_lookup (simulation_id, player_id)
);

-- Add simulation_report to the Articles article_type enum
ALTER TABLE Articles
    MODIFY COLUMN article_type ENUM(
        'power_ranking',
        'team_analysis',
        'rumors',
        'trade_analysis',
        'injury',
        'matchup_analysis',
        'matchup_breakdown',
        'simulation_report'
    );
