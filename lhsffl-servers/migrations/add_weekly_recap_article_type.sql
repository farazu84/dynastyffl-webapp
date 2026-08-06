-- Adds the weekly_recap article type to the Articles enum

ALTER TABLE Articles
    MODIFY article_type ENUM('power_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown', 'weekly_recap') DEFAULT NULL;
