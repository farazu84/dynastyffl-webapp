import requests
import os
from app.models.teams import Teams
from app.models.players import Players
from app.models.league_state import LeagueState
from app.models.team_records import TeamRecords
from app.models.matchups import Matchups
from app import db


def synchronize_matchups():
    '''
    Synchronizes matchups with the Sleeper API for the current week.
    Updates points_for, points_against, and completion status.
    '''
    
    league_state = LeagueState.query.filter_by(current=True).first()
    if not league_state:
        raise ValueError("No current league state found. Please set league state first.")
    
    print(f'Fetching matchups for week {league_state.week}, year {league_state.year}')
    
    try:
        # Fetch matchup data from Sleeper API
        response = requests.get(f'https://api.sleeper.app/v1/league/{os.getenv("LEAGUE_ID")}/matchups/{league_state.week}')
        response.raise_for_status()
        sleeper_matchups = response.json()
        
        if not sleeper_matchups:
            print("No matchup data received from Sleeper API")
            return {'success': True, 'message': 'No matchups to sync'}
        
        # Group matchups by matchup_id to find opponents
        matchup_groups = {}
        for matchup in sleeper_matchups:
            matchup_id = matchup['matchup_id']
            if matchup_id not in matchup_groups:
                matchup_groups[matchup_id] = []
            matchup_groups[matchup_id].append(matchup)
        
        updated_count = 0
        
        # Process each matchup pair
        for matchup_id, teams in matchup_groups.items():
            if len(teams) != 2:
                print(f"Warning: Matchup {matchup_id} has {len(teams)} teams instead of 2")
                continue
            
            team1, team2 = teams
            
            # Update team1's matchup record
            team1_matchup = Matchups.query.filter_by(
                sleeper_roster_id=team1['roster_id'],
                week=league_state.week,
                year=league_state.year
            ).first()
            
            if team1_matchup:
                team1_matchup.points_for = float(team1.get('points', 0))
                team1_matchup.points_against = float(team2.get('points', 0))
                updated_count += 1
                print(f"Updated matchup for roster {team1['roster_id']}: {team1_matchup.points_for} vs {team1_matchup.points_against}")
            else:
                print(f"Warning: No matchup record found for roster {team1['roster_id']} in week {league_state.week}")
            
            # Update team2's matchup record
            team2_matchup = Matchups.query.filter_by(
                sleeper_roster_id=team2['roster_id'],
                week=league_state.week,
                year=league_state.year
            ).first()
            
            if team2_matchup:
                team2_matchup.points_for = float(team2.get('points', 0))
                team2_matchup.points_against = float(team1.get('points', 0))
                updated_count += 1
                print(f"Updated matchup for roster {team2['roster_id']}: {team2_matchup.points_for} vs {team2_matchup.points_against}")
            else:
                print(f"Warning: No matchup record found for roster {team2['roster_id']} in week {league_state.week}")
        
        # Commit all changes
        db.session.commit()
        
        print(f"Successfully updated {updated_count} matchup records for week {league_state.week}")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'week': league_state.week,
            'year': league_state.year
        }
        
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch matchup data from Sleeper API: {e}")
        db.session.rollback()
        raise
        
    except Exception as e:
        print(f"ERROR: Matchup synchronization failed: {e}")
        db.session.rollback()
        raise


def set_league_state():
    '''
    Sets the league state.
    '''

    try:
        get_league_state = requests.get('https://api.sleeper.app/v1/state/nfl')
        get_league_state.raise_for_status()
        league_state = get_league_state.json()

        current_week = league_state['week']
        current_year = int(league_state['season'])

        # Sets previous league state to not current.
        LeagueState.query.filter_by(current=True).update(
            {LeagueState.current: False},
            synchronize_session=False
        )

        # Adds new league state.
        new_league_state = LeagueState(
            year=current_year,
            week=current_week,
            current=True
        )
        db.session.add(new_league_state)
        db.session.commit()
    except requests.RequestException as e:
        db.session.rollback()
        raise
    except Exception as e:
        db.session.rollback()
        raise
        

def synchronize_teams():
    '''
    Synchronizes the teams with the sleeper API.
    This will update the players on each team in the database, along with the starter, bench, and taxi positions.
    Also syncs team records (wins, losses, points for/against) from the roster settings.
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
        
        # Get current league state to determine the year
        current_league_state = LeagueState.query.filter_by(current=True).first()
        if not current_league_state:
            raise ValueError("No current league state found. Please set league state first.")
        
        current_year = current_league_state.year
        
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
            
            # Sync team records from roster settings
            settings = roster.get('settings', {})
            if settings:
                wins = settings.get('wins', 0)
                losses = settings.get('losses', 0)
                
                fpts = settings.get('fpts', 0)
                fpts_decimal = settings.get('fpts_decimal', 0)
                points_for = float(fpts) + (float(fpts_decimal) / 100.0)
                
                fpts_against = settings.get('fpts_against', 0)
                fpts_against_decimal = settings.get('fpts_against_decimal', 0)
                points_against = float(fpts_against) + (float(fpts_against_decimal) / 100.0)
                
                # Check if team record already exists for this year
                existing_record = TeamRecords.query.filter_by(
                    team_id=team.team_id,
                    year=current_year
                ).first()
                
                if existing_record:
                    existing_record.wins = wins
                    existing_record.losses = losses
                    existing_record.points_for = points_for
                    existing_record.points_against = points_against
                    print(f"Updated team record for {team.team_name}: {wins}-{losses}, PF: {points_for:.2f}, PA: {points_against:.2f}")
                else:
                    new_record = TeamRecords(
                        team_id=team.team_id,
                        year=current_year,
                        wins=wins,
                        losses=losses,
                        points_for=points_for,
                        points_against=points_against
                    )
                    db.session.add(new_record)        
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
