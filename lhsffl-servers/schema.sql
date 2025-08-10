CREATE TABLE Users (
    user_id INT unsigned NOT NULL AUTO_INCREMENT,
    user_name VARCHAR(64) NOT NULL,
    first_name VARCHAR(64) NOT NULL DEFAULT '',
    last_name VARCHAR(64) NOT NULL DEFAULT '',
    sleeper_user_id BIGINT unsigned DEFAULT NULL,
    password VARCHAR(64) NOT NULL DEFAULT '',
    admin tinyint(4) NOT NULL DEFAULT '0',
    team_owner tinyint(4) NOT NULL DEFAULT '0',
    PRIMARY KEY (user_id)
);

CREATE TABLE Teams (
    team_id INT unsigned NOT NULL AUTO_INCREMENT,
    team_name VARCHAR(128) NOT NULL DEFAULT '',
    championships INT unsigned NOT NULL DEFAULT 0,
    sleeper_roster_id INT unsigned NOT NULL,
    PRIMARY KEY (team_id)
)

CREATE TABLE TeamOwners (
    team_owner_id INT unsigned NOT NULL AUTO_INCREMENT,
    user_id INT unsigned NOT NULL,
    sleeper_user_id BIGINT unsigned DEFAULT NULL,
    team_id INT unsigned NOT NULL,
    primary_owner tinyint(4) NOT NULL DEFAULT '1',
    PRIMARY KEY (team_owner_id)
)

CREATE TABLE Players (
    player_id INT unsigned NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(64) NOT NULL,
    last_name VARCHAR(64) NOT NULL,
    birth_date VARCHAR(64) DEFAULT NULL,
    team_id INT unsigned DEFAULT NULL,
    nfl_team VARCHAR(64) DEFAULT NULL,
    college VARCHAR(64) DEFAULT NULL,
    sleeper_id INT unsigned NOT NULL,
    years_exp INT unsigned DEFAULT 0,
    position ENUM('QB', 'RB', 'WR', 'TE', 'K') DEFAULT NULL,
    age INT unsigned DEFAULT NULL,
    player_number INT unsigned DEFAULT NULL,
    taxi tinyint(4) NOT NULL DEFAULT '0',
    starter tinyint(4) NOT NULL DEFAULT '0',
    PRIMARY KEY (player_id)
)

CREATE TABLE Articles (
    article_id INT unsigned NOT NULL AUTO_INCREMENT,
    article_type ENUM('power_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown') DEFAULT NULL,
    author VARCHAR(128) DEFAULT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    thumbnail VARCHAR(128) NOT NULL,
    team_id INT unsigned DEFAULT NULL,
    creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (article_id)
)

CREATE TABLE Matchups (
    matchup_id INT unsigned NOT NULL AUTO_INCREMENT,
    year INT NOT NULL,
    week INT NOT NULL, 
    sleeper_matchup_id INT NOT NULL,
    sleeper_roster_id INT NOT NULL,
    opponent_sleeper_roster_id INT NOT NULL,
    PRIMARY KEY (matchup_id)
)