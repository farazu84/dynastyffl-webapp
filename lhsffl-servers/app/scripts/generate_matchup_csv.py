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
    
    # Add unique hash to each matchup
    for matchup_data in matchups_data:
        matchup_id = matchup_data.get('matchup_id', 0)
        unique_hash = generate_matchup_hash(YEAR, week, matchup_id)
        
        # Add the hash and week info to the matchup data
        matchup_data['unique_matchup_hash'] = unique_hash
        matchup_data['year'] = YEAR
        matchup_data['week'] = week
        
        print(f"Week {week}, Matchup {matchup_id} → Hash: {unique_hash}")
    
    matchup.extend(matchups_data)

with open('matchup.json', 'w') as f:
    json.dump(matchup, f)