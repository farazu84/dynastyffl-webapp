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
    year_exp INT unsigned DEFAULT 0,
    position ENUM('QB', 'RB', 'WR', 'TE', 'K') DEFAULT NULL,
    age INT unsigned DEFAULT NULL,
    player_number INT unsigned DEFAULT NULL,
    taxi tinyint(4) NOT NULL DEFAULT '0',
    starter tinyint(4) NOT NULL DEFAULT '0',
    PRIMARY KEY (player_id)
)