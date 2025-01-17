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
    drop_users = '''DROP TABLE Users;'''
    drop_teams = '''DROP TABLE Teams;'''
    drop_team_owners = '''DROP TABLE TeamOwners'''
    drop_players = '''DROP TABLE Players'''

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

    tables.append(users_table)
    tables.append(teams_table)
    tables.append(team_owners_table)
    tables.append(players_table)

    for table_query in tables:
        cursor.execute(table_query)

def import_users_and_teams():
    '''
    Imports the users and teams from the Sleeper user API.
    '''
    user_json_file = open('user.json', 'r')
    user_json_data = json.load(user_json_file)


    team_query = 'INSERT INTO Teams (team_name, championships) VALUES '
    user_query = 'INSERT INTO Users (user_name, sleeper_user_id, team_owner) VALUES '

    for user in user_json_data:
        user_query += f"""("{user.get('display_name')}", {user['user_id']}, 1),"""
        if 'team_name' in user['metadata']:
            team_query += f"""("{user['metadata']['team_name']}", 0),"""


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
        if player['position'] in ['QB', 'RB', 'WR', 'TE', 'K'] and player['status'] == 'Active':
            team =  f'"{player["team"]}"' if player["team"] else "NULL"
            college = f'"{player["college"]}"' if player["college"] else "NULL"
            number = player['number'] if player['number'] else 0
            age = player['age'] if player['age'] else 0
            birth_date = f'"{player["birth_date"]}"' if player["birth_date"] else "NULL"
            player_query += f"""("{player['first_name']}", "{player['last_name']}", {birth_date}, NULL, {team}, {college}, {int(player['player_id'])}, {player['years_exp']}, "{player['position']}", {age}, {number}, 0),"""

    player_query = player_query[:-1]

    player_query += ';'

    players_json_file.close()

    return player_query

def update_team_owners(cursor, connection):
    user_json_file = open('user.json', 'r')
    user_json_data = json.load(user_json_file)

    user_to_team = {}
    
    get_users = '''
                SELECT *
                FROM Users;
                '''
    cursor.execute(get_users)
    for (user_id, user_name, _, _, sleeper_user_id, _, _, _) in cursor:
        user_to_team[user_name] = {'id': user_id, 'sleeper_id': sleeper_user_id}

    for user in user_json_data:
        if 'team_name' in user['metadata']:
            user_to_team[user.get('display_name')]['team'] = user['metadata']['team_name']


    get_teams = '''
                SELECT *
                FROM Teams;
                '''
    cursor.execute(get_teams)
    for (team_id, team_name, championships) in cursor:
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
        for starters in roster['starters']:
            query = f'UPDATE Players SET starter = 1, team_id = {team} WHERE sleeper_id = {starters};'
            execute_query(cursor, connection, query)
        for players in roster['players']:
            query = f'UPDATE Players SET team_id = {team} WHERE sleeper_id = {players};'
            execute_query(cursor, connection, query)
        for reserves in roster['taxi']:
            query = f'UPDATE Players SET taxi = 1, team_id = {team} WHERE sleeper_id = {reserves};'
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
