import requests
import os
from app.models.teams import Teams
from app.models.players import Players
from app import db

def synchronize_teams():
    '''
    Synchronizes the teams with the sleeper API.
    This will update the players on each team in the database, along with the starter, bench, and taxi postions.
    Uses a single transaction with rollback capability for data integrity.
    '''
    print(f'Fetching rosters from: https://api.sleeper.app/v1/league/{os.getenv("LEAGUE_ID")}/rosters')
    
    try:
        # Fetch roster data from Sleeper API
        request = requests.get(f'https://api.sleeper.app/v1/league/{os.getenv("LEAGUE_ID")}/rosters')
        request.raise_for_status()  # Raise exception for bad HTTP status
        rosters = request.json()
        
        if not rosters:
            raise ValueError("No roster data received from Sleeper API")
        
        
        # First, reset all players to not be on any team and clear positions
        reset_count = Players.query.update({
            Players.team_id: None,
            Players.starter: False,
            Players.taxi: False
        })
        
        for roster in rosters:
            team = Teams.query.filter_by(sleeper_roster_id=roster['roster_id']).first()
            if not team:
                continue
            
            all_player_ids = roster.get('players', [])
            starter_ids = roster.get('starters', [])
            taxi_ids = roster.get('taxi', [])

            if all_player_ids:
                all_player_ids_int = [int(pid) for pid in all_player_ids if pid]
                players_updated = Players.query.filter(Players.sleeper_id.in_(all_player_ids_int)).update(
                    {Players.team_id: team.team_id}, 
                    synchronize_session=False
                )
            
            if starter_ids:
                starter_ids_int = [int(pid) for pid in starter_ids if pid]
                starters_updated = Players.query.filter(Players.sleeper_id.in_(starter_ids_int)).update(
                    {Players.starter: True}, 
                    synchronize_session=False
                )
            
            if taxi_ids:
                taxi_ids_int = [int(pid) for pid in taxi_ids if pid]
                taxi_updated = Players.query.filter(Players.sleeper_id.in_(taxi_ids_int)).update(
                    {Players.taxi: True}, 
                    synchronize_session=False
                )
        
        # Commit all changes in one transaction
        db.session.commit()
        
        return {
            'success': True
        }
        
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch roster data from Sleeper API: {e}")
        db.session.rollback()
        raise
        
    except ValueError as e:
        print(f"ERROR: Invalid data received: {e}")
        db.session.rollback()
        raise
        
    except Exception as e:
        print(f"ERROR: Database operation failed: {e}")
        print("Rolling back all changes...")
        db.session.rollback()
        print("All changes have been rolled back.")
        raise
