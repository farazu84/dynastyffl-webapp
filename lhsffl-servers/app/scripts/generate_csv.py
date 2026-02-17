import requests
import os
import json

old_league_id = 1063040492125937664
league_id = 1328498202462126080

league_users_url = f'https://api.sleeper.app/v1/league/{league_id}/users'
roster_url = f'https://api.sleeper.app/v1/league/{league_id}/rosters'
matchup_url = f'https://api.sleeper.app/v1/league/{league_id}/matchups/1'
#players_url = 'https://api.sleeper.app/v1/players/nfl'
#league_users = requests.get(league_users_url)
#league_roster = requests.get(roster_url)
league_matchup = requests.get(matchup_url)
#players = requests.get(players_url)

'''
with open('user.json', 'w') as f:
    json.dump(league_users.json(), f)

with open('roster.json', 'w') as f:
    json.dump(league_roster.json(), f)
'''
with open('matchup.json', 'w') as f:
    json.dump(league_matchup.json(), f)

#with open('players.json', 'w') as f:
#    json.dump(players.json(), f)