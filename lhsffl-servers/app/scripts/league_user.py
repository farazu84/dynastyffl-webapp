import mysql.connector
import requests
import os
import json
from dotenv import load_dotenv

def setupConnection():
    '''
    Setups up connection to the DB and returns a connection cursor object.
    '''
    load_dotenv()

    server_user = os.getenv('SQL_USER')
    password = os.getenv('SQL_PASSWORD')
    host = os.getenv('SQL_HOST')
    database = os.getenv('DB_NAME')

    mydb = mysql.connector.connect(
        host=host,
        user=server_user,
        password=password,
        database=database,
        auth_plugin='mysql_native_password'
    )

    return mydb

def drop_tables(cursor):
    '''
    Drops existing tables.
    '''
    tables = []
    drop_users = '''DROP TABLE IF EXISTS Users;'''
    drop_teams = '''DROP TABLE IF EXISTS Teams;'''
    drop_team_owners = '''DROP TABLE IF EXISTS TeamOwners;'''
    drop_players = '''DROP TABLE IF EXISTS Players;'''

    tables.append(drop_users)
    tables.append(drop_teams)
    tables.append(drop_team_owners)
    tables.append(drop_players)

    for table in tables:
        cursor.execute(table)

def create_tables(cursor):
    '''
    Setups up the tables for the database.
    '''
    tables = []

    users_table = '''
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
                    '''

    teams_table = '''
                    CREATE TABLE Teams (
                    team_id INT unsigned NOT NULL AUTO_INCREMENT,
                    team_name VARCHAR(128) NOT NULL DEFAULT '',
                    championships INT unsigned NOT NULL DEFAULT 0,
                    sleeper_roster_id INT unsigned NOT NULL,
                    PRIMARY KEY (team_id)
                )
                 '''
    
    team_owners_table = '''
                        CREATE TABLE TeamOwners (
                        team_owner_id INT unsigned NOT NULL AUTO_INCREMENT,
                        user_id INT unsigned NOT NULL,
                        sleeper_user_id BIGINT unsigned DEFAULT NULL,
                        team_id INT unsigned NOT NULL,
                        primary_owner tinyint(4) NOT NULL DEFAULT '1',
                        PRIMARY KEY (team_owner_id)
                    )
                        '''

    players_table = '''
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
                    '''

    article_table = '''
                    CREATE TABLE Articles (
                        article_id INT unsigned NOT NULL AUTO_INCREMENT,
                        article_type ENUM('power_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown') DEFAULT NULL,
                        author VARCHAR(128) DEFAULT NULL,
                        title TINYTEXT NOT NULL,
                        content TEXT NOT NULL,
                        thumbnail VARCHAR(128) NOT NULL,
                        team_id INT unsigned DEFAULT NULL,
                        creation_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (article_id)
                    )
                    '''

    tables.append(users_table)
    tables.append(teams_table)
    tables.append(team_owners_table)
    tables.append(players_table)
    #tables.append(article_table)

    for table_query in tables:
        cursor.execute(table_query)

def import_users_and_teams():
    '''
    Imports the users and teams from the Sleeper user API.
    '''
    user_json_file = open('user.json', 'r')
    user_json_data = json.load(user_json_file)
    
    # Load roster data to see which users have active rosters
    roster_json_file = open('roster.json', 'r')
    roster_json_data = json.load(roster_json_file)
    roster_json_file.close()
    
    # Create mapping of owner_id to roster_id
    owner_to_roster = {str(roster['owner_id']): roster['roster_id'] for roster in roster_json_data}

    team_query = 'INSERT INTO Teams (team_name, championships, sleeper_roster_id) VALUES '
    user_query = 'INSERT INTO Users (user_name, sleeper_user_id, team_owner) VALUES '

    for user in user_json_data:
        user_query += f"""("{user.get('display_name')}", {user['user_id']}, 1),"""
        
        # Check if user has active roster
        if user['user_id'] in owner_to_roster:
            roster_id = owner_to_roster[user['user_id']]
            if 'team_name' in user['metadata']:
                team_query += f"""("{user['metadata']['team_name']}", 0, {roster_id}),"""
            else:
                # Create default team name for users with rosters but no team name
                default_team_name = f"{user.get('display_name')}'s Team"
                team_query += f"""("{default_team_name}", 0, {roster_id}),"""

    user_query = user_query[:-1]
    team_query = team_query[:-1]

    user_query += ';'
    team_query += ';'

    user_json_file.close()

    return user_query, team_query

def import_players():
    '''
    Imports player from Sleeper players API.
    '''
    players_json_file = open('players.json', 'r')
    players_json_data = json.load(players_json_file)

    player_query = 'INSERT INTO Players (first_name,last_name,birth_date,team_id,nfl_team,college,sleeper_id,year_exp,position,age,player_number,taxi) VALUES '

    for player_id, player in players_json_data.items():
        if player.get('position') in ['QB', 'RB', 'WR', 'TE', 'K'] and player.get('status') == 'Active':
            team = f'"{player["team"]}"' if player.get("team") and player["team"] is not None else "NULL"
            college = f'"{player["college"]}"' if player.get("college") and player["college"] is not None else "NULL"
            number = player['number'] if player.get('number') and player['number'] is not None else 0
            age = player['age'] if player.get('age') and player['age'] is not None else 0
            birth_date = f'"{player["birth_date"]}"' if player.get("birth_date") and player["birth_date"] is not None else "NULL"
            first_name = player.get('first_name', '')
            last_name = player.get('last_name', '')
            years_exp = player.get('years_exp', 0) if player.get('years_exp') is not None else 0
            position = player.get('position', '')
            player_id_val = int(player['player_id']) if player.get('player_id') else 0
            player_query += f"""("{first_name}", "{last_name}", {birth_date}, NULL, {team}, {college}, {player_id_val}, {years_exp}, "{position}", {age}, {number}, 0),"""

    player_query = player_query[:-1]

    player_query += ';'

    players_json_file.close()

    return player_query

def update_team_owners(cursor, connection):
    user_json_file = open('user.json', 'r')
    user_json_data = json.load(user_json_file)
    
    # Load roster data to see which users have active rosters
    roster_json_file = open('roster.json', 'r')
    roster_json_data = json.load(roster_json_file)
    roster_json_file.close()
    
    # Get list of active roster owner IDs
    active_owners = {str(roster['owner_id']) for roster in roster_json_data}

    user_to_team = {}
    
    get_users = '''
                SELECT *
                FROM Users;
                '''
    cursor.execute(get_users)
    for (user_id, user_name, _, _, sleeper_user_id, _, _, _) in cursor:
        user_to_team[user_name] = {'id': user_id, 'sleeper_id': sleeper_user_id}

    for user in user_json_data:
        # Check if user has active roster
        if user['user_id'] in active_owners:
            if 'team_name' in user['metadata']:
                user_to_team[user.get('display_name')]['team'] = user['metadata']['team_name']
            else:
                # Create default team name for users with rosters but no team name
                default_team_name = f"{user.get('display_name')}'s Team"
                user_to_team[user.get('display_name')]['team'] = default_team_name

    get_teams = '''
                SELECT *
                FROM Teams;
                '''
    cursor.execute(get_teams)
    for (team_id, team_name, championships, sleeper_roster_id) in cursor:
        for user, values in user_to_team.items():
            if 'team' in values and values['team'] == team_name:
                values['team_id'] = team_id

    team_owners = 'INSERT INTO TeamOwners(user_id,sleeper_user_id,team_id) VALUES '
    for user, values in user_to_team.items():
        if 'team' in values:
            print(values)
            team_owners += f'''({values['id']}, {values['sleeper_id']}, {values['team_id']}),'''

    team_owners = team_owners[:-1]
    team_owners += ';'

    user_json_file.close()

    return team_owners

def update_teams(cursor, connection):
    roster_json_file = open('roster.json', 'r')
    roster_json_data = json.load(roster_json_file)
    update_queries = []

    for roster in roster_json_data:
        team = None
        get_teams = f'SELECT * FROM TeamOwners WHERE sleeper_user_id = {roster["owner_id"]}'
        cursor.execute(get_teams)
        for (_, user_id, _, team_id, _) in cursor:
            team = team_id
        
        # Convert None to NULL for SQL
        team_value = team if team is not None else "NULL"
        
        for starters in roster['starters']:
            query = f'UPDATE Players SET starter = 1, team_id = {team_value} WHERE sleeper_id = {starters};'
            print(query)
            execute_query(cursor, connection, query)
        for players in roster['players']:
            query = f'UPDATE Players SET team_id = {team_value} WHERE sleeper_id = {players};'
            execute_query(cursor, connection, query)
        for reserves in roster['taxi']:
            query = f'UPDATE Players SET taxi = 1, team_id = {team_value} WHERE sleeper_id = {reserves};'
            execute_query(cursor, connection, query)

def execute_query(cursor, connection, query):
    cursor.execute(query)
    connection.commit()



if __name__ == '__main__':
    connection = setupConnection()
    cursor = connection.cursor()
    drop_tables(cursor)
    create_tables(cursor)
    users_query, teams_query = import_users_and_teams()
    players_query = import_players()
    execute_query(cursor, connection, users_query)
    execute_query(cursor, connection, teams_query)
    execute_query(cursor, connection, players_query)
    owners_query = update_team_owners(cursor, connection)
    execute_query(cursor, connection, owners_query)
    update_teams(cursor, connection)
    connection.close()
    cursor.close()
