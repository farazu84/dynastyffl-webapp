-- Performance indexes for teams endpoint optimization

-- Index for TeamRecords ordering (wins DESC, points_for DESC)
CREATE INDEX idx_team_records_performance ON TeamRecords (wins DESC, points_for DESC);

-- Index for team_id foreign key in TeamRecords (if not already exists)
CREATE INDEX idx_team_records_team_id ON TeamRecords (team_id);

-- Index for current year lookup in TeamRecords
CREATE INDEX idx_team_records_year ON TeamRecords (year);

-- Composite index for team_id + year (for current_team_record property)
CREATE INDEX idx_team_records_team_year ON TeamRecords (team_id, year);

-- Index for LeagueState current lookup
CREATE INDEX idx_league_state_current ON LeagueState (current);

-- Index for sleeper_roster_id in Teams (used in matchups)
CREATE INDEX idx_teams_sleeper_roster_id ON Teams (sleeper_roster_id);

ALTER TABLE TeamOwners ADD INDEX idx_team_owners_team_id (team_id);
ALTER TABLE TeamOwners ADD INDEX idx_team_owners_user_id (user_id);
ALTER TABLE Players ADD INDEX idx_players_team_id (team_id);
ALTER TABLE ArticleTeams ADD INDEX idx_article_teams_team_id (team_id);
ALTER TABLE ArticleTeams ADD INDEX idx_article_teams_article_id (article_id);

-- Matchups performance indexes
CREATE INDEX idx_matchups_week ON Matchups (week);
CREATE INDEX idx_matchups_year ON Matchups (year);
CREATE INDEX idx_matchups_week_year ON Matchups (week, year);
CREATE INDEX idx_matchups_sleeper_roster_id ON Matchups (sleeper_roster_id);
CREATE INDEX idx_matchups_sleeper_roster_week ON Matchups (sleeper_roster_id, week);
CREATE INDEX idx_matchups_sleeper_matchup_id ON Matchups (sleeper_matchup_id);
CREATE INDEX idx_matchups_current_lookup ON Matchups (year, week, sleeper_matchup_id);
