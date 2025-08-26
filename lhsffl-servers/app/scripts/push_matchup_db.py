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
    prod_user = os.getenv('PROD_DYNASTY_DB_USER')
    prod_password = os.getenv('PROD_DYNASTY_DB_PASSWORD')
    prod_host = os.getenv('PROD_SQL_HOST')
    prod_database = os.getenv('PROD_DB_NAME')

    mydb = mysql.connector.connect(
        host=host,
        user=server_user,
        password=password,
        database=database,
        auth_plugin='mysql_native_password'
    )

    prod_db = mysql.connector.connect(
        host=prod_host,
        user=prod_user,
        password=prod_password,
        database=prod_database,
        port=3307,
        auth_plugin='mysql_native_password'
    )

    return prod_db

def drop_tables(cursor):
    '''
    Drops existing tables.
    '''
    tables = []
    drop_matchups = '''DROP TABLE IF EXISTS Matchups;'''

    tables.append(drop_matchups)
    for table in tables:
        cursor.execute(table)

def create_tables(cursor):
    '''
    Creates the Matchups table using YOUR schema definition from schema.sql
    '''
    matchups_table = '''
                    CREATE TABLE Matchups (
                        matchup_id INT unsigned NOT NULL AUTO_INCREMENT,
                        year INT NOT NULL,
                        week INT NOT NULL, 
                        sleeper_matchup_id INT NOT NULL,
                        sleeper_roster_id INT NOT NULL,
                        opponent_sleeper_roster_id INT NOT NULL,
                        PRIMARY KEY (matchup_id)
                    )
                    '''
    cursor.execute(matchups_table)

def import_matchups(cursor, connection):
    '''
    Imports matchup data from matchup.json file into YOUR table schema.
    '''
    with open('matchup.json', 'r') as f:
        matchups_data = json.load(f)
    
    insert_query = '''
        INSERT INTO Matchups (
            year, week, sleeper_matchup_id, sleeper_roster_id, opponent_sleeper_roster_id
        ) VALUES (%s, %s, %s, %s, %s)
    '''
    
    for matchup in matchups_data:
        values = (
            matchup.get('year'),
            matchup.get('week'),
            matchup.get('matchup_id'),  # maps to sleeper_matchup_id
            matchup.get('roster_id'),   # maps to sleeper_roster_id
            matchup.get('opponent_sleeper_roster_id')
        )
        
        cursor.execute(insert_query, values)
        print(f"Inserted: Week {matchup.get('week')}, Matchup {matchup.get('matchup_id')}, Roster {matchup.get('roster_id')} vs {matchup.get('opponent_sleeper_roster_id')}")
    
    connection.commit()

def execute_query(cursor, connection, query):
    cursor.execute(query)
    connection.commit()

if __name__ == '__main__':
    connection = setupConnection()
    cursor = connection.cursor()
    
    print("Dropping existing Matchups table...")
    drop_tables(cursor)
    
    print("Creating Matchups table with YOUR schema...")
    create_tables(cursor)
    
    print("Importing matchup data...")
    import_matchups(cursor, connection)
    
    print("Import completed!")
    connection.close()