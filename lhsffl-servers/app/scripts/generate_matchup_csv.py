import requests
import os
import json

LEAGUE_ID = 1195252934627844096
YEAR = 2025  # Set your league year

def generate_matchup_hash(year, week, matchup_id):
    """Generate unique integer hash: year(4) + week(2) + matchup_id(2)"""
    return (year * 10000) + (week * 100) + matchup_id

matchup = []

for week in range(1, 15):
    matchup_url = f'https://api.sleeper.app/v1/league/{LEAGUE_ID}/matchups/{week}'
    
    league_matchup = requests.get(matchup_url)
    matchups_data = league_matchup.json()
    
    # Create a mapping of matchup_id to roster_ids for finding opponents
    matchup_to_rosters = {}
    for matchup_data in matchups_data:
        matchup_id = matchup_data.get('matchup_id', 0)
        roster_id = matchup_data.get('roster_id', 0)
        
        if matchup_id not in matchup_to_rosters:
            matchup_to_rosters[matchup_id] = []
        matchup_to_rosters[matchup_id].append(roster_id)
    
    # Add unique hash and opponent info to each matchup
    for matchup_data in matchups_data:
        matchup_id = matchup_data.get('matchup_id', 0)
        roster_id = matchup_data.get('roster_id', 0)
        
        # Find opponent's roster_id (the other team in the same matchup)
        opponents = [r for r in matchup_to_rosters[matchup_id] if r != roster_id]
        opponent_roster_id = opponents[0] if opponents else None
        
        unique_hash = generate_matchup_hash(YEAR, week, matchup_id)
        
        # Add the hash, week info, and opponent info to the matchup data
        matchup_data['unique_matchup_hash'] = unique_hash
        matchup_data['year'] = YEAR
        matchup_data['week'] = week
        matchup_data['opponent_sleeper_roster_id'] = opponent_roster_id
        
        print(f"Week {week}, Matchup {matchup_id} → Hash: {unique_hash}")
    
    matchup.extend(matchups_data)

with open('matchup.json', 'w') as f:
    json.dump(matchup, f)