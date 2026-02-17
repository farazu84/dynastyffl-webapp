import requests
import os
import json
from app.models.teams import Teams
from app.models.players import Players
from app.models.league_state import LeagueState
from app.models.team_records import TeamRecords
from app.models.matchups import Matchups
from app import db


def synchronize_players():
    '''
    Synchronizes players with local players.json file (for testing to avoid API limits).
    Updates existing players and adds new ones based on sleeper_id.
    Syncs all fields from height onwards as specified.
    
    NOTE: Currently uses local players.json instead of Sleeper API to avoid rate limits during testing.
    '''
    
    try:
        # Choose data source: local file for testing or API for production
        use_local_file = os.getenv('USE_LOCAL_PLAYERS_JSON', 'true').lower() == 'true'
        
        if use_local_file:
            # Load player data from local JSON file (for testing to avoid API limits)
            players_json_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', 'players.json')
            
            print(f"Loading player data from: {players_json_path}")
            
            try:
                with open(players_json_path, 'r') as players_file:
                    sleeper_players = json.load(players_file)
            except FileNotFoundError:
                print(f"ERROR: players.json not found at {players_json_path}")
                print("Please ensure players.json exists in the scripts directory")
                return {'success': False, 'message': 'players.json file not found'}
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON in players.json: {e}")
                return {'success': False, 'message': 'Invalid JSON in players.json'}
        else:
            # Use Sleeper API (for production)
            print("Fetching player data from Sleeper API...")
            response = requests.get('https://api.sleeper.app/v1/players/nfl')
            response.raise_for_status()
            sleeper_players = response.json()
        
        if not sleeper_players:
            source = "players.json" if use_local_file else "Sleeper API"
            print(f"No player data found from {source}")
            return {'success': True, 'message': 'No players to sync'}
        
        source = "players.json" if use_local_file else "Sleeper API"
        print(f"Loaded {len(sleeper_players)} players from {source}")
        
        # Filter for active players in relevant positions
        relevant_players = {}
        for player_id, player in sleeper_players.items():
            if (player.get('position') in ['QB', 'RB', 'WR', 'TE', 'K'] and 
                player.get('status') == 'Active'):
                relevant_players[player_id] = player
        
        print(f"Processing {len(relevant_players)} relevant active players")
        
        updated_count = 0
        added_count = 0
        batch_size = 100  # Process in batches to avoid memory issues
        current_batch = 0
        
        for sleeper_id, player_data in relevant_players.items():
            current_batch += 1
            try:
                # Check if player exists in database
                existing_player = Players.query.filter_by(sleeper_id=int(sleeper_id)).first()
                
                # Helper functions for safe data conversion
                def safe_str(val, max_length=None):
                    if val is None:
                        return None
                    str_val = str(val)
                    if max_length and len(str_val) > max_length:
                        str_val = str_val[:max_length]
                    return str_val
                
                def safe_int(val):
                    if val is None:
                        return None
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        return None
                
                def safe_bool(val):
                    if val is None:
                        return None
                    return bool(val)
                
                # Extract and format player data (focusing on height onwards as requested)
                height = safe_str(player_data.get('height'), 10)
                weight = safe_int(player_data.get('weight'))
                high_school = safe_str(player_data.get('high_school'), 128)
                status = safe_str(player_data.get('status'))
                active = safe_bool(player_data.get('active'))
                depth_chart_order = safe_int(player_data.get('depth_chart_order'))
                injury_status = safe_str(player_data.get('injury_status'), 64)
                injury_body_part = safe_str(player_data.get('injury_body_part'), 64)
                injury_start_date = safe_str(player_data.get('injury_start_date'))
                practice_participation = safe_str(player_data.get('practice_participation'), 32)
                espn_id = safe_int(player_data.get('espn_id'))
                yahoo_id = safe_int(player_data.get('yahoo_id'))
                fantasy_data_id = safe_int(player_data.get('fantasy_data_id'))
                rotowire_id = safe_int(player_data.get('rotowire_id'))
                rotoworld_id = safe_int(player_data.get('rotoworld_id'))
                sportradar_id = safe_str(player_data.get('sportradar_id'), 64)
                stats_id = safe_int(player_data.get('stats_id'))
                gsis_id = safe_str(player_data.get('gsis_id'), 32)
                oddsjam_id = safe_int(player_data.get('oddsjam_id'))
                pandascore_id = safe_int(player_data.get('pandascore_id'))
                opta_id = safe_int(player_data.get('opta_id'))
                swish_id = safe_int(player_data.get('swish_id'))
                
                # Also get basic fields for new player creation
                first_name = safe_str(player_data.get('first_name', ''), 64)
                last_name = safe_str(player_data.get('last_name', ''), 64)
                birth_date = safe_str(player_data.get('birth_date'), 64)
                nfl_team = safe_str(player_data.get('team'), 64)
                college = safe_str(player_data.get('college'), 64)
                years_exp = safe_int(player_data.get('years_exp')) or 0
                position = safe_str(player_data.get('position'))
                age = safe_int(player_data.get('age')) or 0
                player_number = safe_int(player_data.get('number')) or 0
                
                if existing_player:
                    # Use bulk update for better performance and to avoid session issues
                    try:
                        Players.query.filter_by(sleeper_id=int(sleeper_id)).update({
                            Players.nfl_team: nfl_team,
                            Players.age: age,
                            Players.player_number: player_number,
                            Players.years_exp: years_exp,
                            Players.height: height,
                            Players.weight: weight,
                            Players.high_school: high_school,
                            Players.status: status,
                            Players.active: active,
                            Players.depth_chart_order: depth_chart_order,
                            Players.injury_status: injury_status,
                            Players.injury_body_part: injury_body_part,
                            Players.injury_start_date: injury_start_date,
                            Players.practice_participation: practice_participation,
                            Players.espn_id: espn_id,
                            Players.yahoo_id: yahoo_id,
                            Players.fantasy_data_id: fantasy_data_id,
                            Players.rotowire_id: rotowire_id,
                            Players.rotoworld_id: rotoworld_id,
                            Players.sportradar_id: sportradar_id,
                            Players.stats_id: stats_id,
                            Players.gsis_id: gsis_id,
                            Players.oddsjam_id: oddsjam_id,
                            Players.pandascore_id: pandascore_id,
                            Players.opta_id: opta_id,
                            Players.swish_id: swish_id
                        }, synchronize_session=False)
                        
                        updated_count += 1
                        print(f"Updated player: {first_name} {last_name} (ID: {sleeper_id})")
                        
                    except Exception as update_error:
                        print(f"Error updating player {sleeper_id} ({first_name} {last_name}): {update_error}")
                        # Continue with next player instead of failing entire sync
                        continue
                    
                else:
                    # Create new player
                    new_player = Players(
                        first_name=first_name,
                        last_name=last_name,
                        birth_date=birth_date,
                        team_id=None,  # Will be set during team sync
                        nfl_team=nfl_team,
                        college=college,
                        sleeper_id=int(sleeper_id),
                        years_exp=years_exp,
                        position=position,
                        age=age,
                        player_number=player_number,
                        taxi=False,
                        starter=False,
                        # Fields from height onwards
                        height=height,
                        weight=weight,
                        high_school=high_school,
                        status=status,
                        active=active,
                        depth_chart_order=depth_chart_order,
                        injury_status=injury_status,
                        injury_body_part=injury_body_part,
                        injury_start_date=injury_start_date,
                        practice_participation=practice_participation,
                        espn_id=espn_id,
                        yahoo_id=yahoo_id,
                        fantasy_data_id=fantasy_data_id,
                        rotowire_id=rotowire_id,
                        rotoworld_id=rotoworld_id,
                        sportradar_id=sportradar_id,
                        stats_id=stats_id,
                        gsis_id=gsis_id,
                        oddsjam_id=oddsjam_id,
                        pandascore_id=pandascore_id,
                        opta_id=opta_id,
                        swish_id=swish_id
                    )
                    
                    db.session.add(new_player)
                    added_count += 1
                    print(f"Added new player: {first_name} {last_name} (ID: {sleeper_id})")
                
                # Flush every batch to ensure changes are persisted incrementally
                if current_batch % batch_size == 0:
                    db.session.flush()
                    print(f"Flushed batch {current_batch // batch_size} ({current_batch} players processed)")
                    
            except Exception as e:
                print(f"Error processing player {sleeper_id} ({player_data.get('first_name')} {player_data.get('last_name')}): {e}")
                continue
        
        # Final flush for any remaining changes
        db.session.flush()
        
        # Commit all changes
        db.session.commit()
        
        print(f"Player synchronization completed: {updated_count} updated, {added_count} added")
        
        return {
            'success': True,
            'updated_count': updated_count,
            'added_count': added_count,
            'total_processed': len(relevant_players)
        }
        
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"ERROR: Failed to load player data from local file: {e}")
        db.session.rollback()
        raise
    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch player data from Sleeper API: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        print(f"ERROR: Player synchronization failed: {e}")
        db.session.rollback()
        raise


def synchronize_matchups():
    '''
    Synchronizes matchups with the Sleeper API for the current week.
    Updates points_for, points_against, and completion status.
    '''
    
    league_state = LeagueState.query.filter_by(current=True).first()
    if not league_state:
        raise ValueError("No current league state found. Please set league state first.")
    
    league_id = os.getenv('LEAGUE_ID')
    if not league_id:
        raise RuntimeError("LEAGUE_ID environment variable is not set")

    print(f'Fetching matchups for week {league_state.week}, year {league_state.year}')

    try:
        # Fetch matchup data from Sleeper API
        response = requests.get(f'https://api.sleeper.app/v1/league/{league_id}/matchups/{league_state.week}')
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

        league_state = LeagueState.query.filter_by(current=True).first()

        if not (league_state.week == current_week and league_state.year == current_year):
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
    league_id = os.getenv('LEAGUE_ID')
    if not league_id:
        raise RuntimeError("LEAGUE_ID environment variable is not set")

    print(f'Fetching rosters from: https://api.sleeper.app/v1/league/{league_id}/rosters')

    try:
        # Fetch roster data from Sleeper API
        request = requests.get(f'https://api.sleeper.app/v1/league/{league_id}/rosters')
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
