from flask import Blueprint, jsonify
from sqlalchemy import func
from app.models.teams import Teams
from app.models.matchups import Matchups
from app.models.team_records import TeamRecords
from app.models.playoff_matchups import PlayoffMatchups
from app.models.player_weekly_stats import PlayerWeeklyStats
from app.models.players import Players
from app.models.schemas.users import UsersJSONSchema
from app import db
from app.league_state_manager import get_current_year, get_current_week

teams = Blueprint('teams', __name__)

@teams.route('/teams/all_time', methods=['GET', 'OPTIONS'])
def get_all_time_records():
    """All-time aggregate records (W-L, PF, PA) per team across every season."""
    # Group by all non-aggregated columns so ONLY_FULL_GROUP_BY (MySQL default)
    # doesn't reject the query. outerjoin keeps teams that have no records yet.
    rows = db.session.query(
        Teams,
        func.sum(TeamRecords.wins),
        func.sum(TeamRecords.losses),
        func.sum(TeamRecords.points_for),
        func.sum(TeamRecords.points_against),
    ).outerjoin(TeamRecords, Teams.team_id == TeamRecords.team_id) \
     .group_by(Teams.team_id, Teams.team_name, Teams.championships, Teams.sleeper_roster_id) \
     .order_by(
        func.sum(TeamRecords.wins).desc(),
        func.sum(TeamRecords.points_for).desc()
     ).all()

    teams_data = []
    for team, wins, losses, points_for, points_against in rows:
        teams_data.append({
            'team_id': team.team_id,
            'team_name': team.team_name,
            'championships': team.championships,
            'owners': UsersJSONSchema(many=True).dump(team.owners),
            'all_time_record': {
                'wins': int(wins or 0),
                'losses': int(losses or 0),
                'points_for': float(points_for or 0),
                'points_against': float(points_against or 0),
            },
        })

    return jsonify(success=True, teams=teams_data)

@teams.route('/teams/recent_champions', methods=['GET', 'OPTIONS'])
def get_recent_champions():
    """The last 5 league champions with their record (W-L, PF, PA) from that season."""
    from app.logic.history import champion_roster_by_year

    champ_by_year = champion_roster_by_year()
    recent_years = sorted(champ_by_year.keys(), reverse=True)[:5]

    champions = []
    for year in recent_years:
        roster_id = champ_by_year[year]
        team = Teams.query.filter_by(sleeper_roster_id=roster_id).first()
        if not team:
            continue
        record = TeamRecords.query.filter_by(team_id=team.team_id, year=year).first()
        champions.append({
            'year': year,
            'team_id': team.team_id,
            'team_name': team.team_name,
            'owners': UsersJSONSchema(many=True).dump(team.owners),
            'season_record': {
                'wins': int(record.wins) if record else 0,
                'losses': int(record.losses) if record else 0,
                'points_for': float(record.points_for) if record else 0.0,
                'points_against': float(record.points_against) if record else 0.0,
            },
        })

    return jsonify(success=True, champions=champions)

@teams.route('/teams/champions/<int:year>', methods=['GET', 'OPTIONS'])
def get_championship_run(year):
    """The full story of one season's title: winners bracket, run leaders, big games, title box score."""
    from app.logic.history import champion_roster_by_year

    champ_by_year = champion_roster_by_year()
    champ_roster_id = champ_by_year.get(year)
    if champ_roster_id is None:
        return jsonify(success=False, error=f'No champion recorded for {year}'), 404

    # roster_id -> {team_id, team_name}
    team_by_roster = {
        t.sleeper_roster_id: {'team_id': t.team_id, 'team_name': t.team_name}
        for t in Teams.query.all()
    }
    champ_team = Teams.query.filter_by(sleeper_roster_id=champ_roster_id).first()

    # Playoff seed = rank in that season's standings (wins desc, points_for desc).
    standings = (TeamRecords.query.filter_by(year=year)
                 .order_by(TeamRecords.wins.desc(), TeamRecords.points_for.desc())
                 .all())
    seed_by_team_id = {r.team_id: i + 1 for i, r in enumerate(standings)}

    def team_blob(roster_id, points):
        info = team_by_roster.get(roster_id) or {}
        return {
            'team_id': info.get('team_id'),
            'roster_id': roster_id,
            'name': info.get('team_name'),
            'seed': seed_by_team_id.get(info.get('team_id')),
            'points': points,
        }

    # Score + week for a (roster, opponent) bracket pairing, pulled from Matchups.
    score_rows = Matchups.query.filter_by(year=year).all()
    score_by_pair = {
        (m.sleeper_roster_id, m.opponent_sleeper_roster_id): m
        for m in score_rows
    }

    # ── Full winners bracket, grouped by round ──────────────────────────────
    winners = (PlayoffMatchups.query
               .filter_by(year=year, bracket='winners')
               .order_by(PlayoffMatchups.round, PlayoffMatchups.sleeper_matchup_id)
               .all())

    # Championship game: placement == 1, else the highest-round game.
    title_match = next((m for m in winners if m.placement == 1), None)
    if title_match is None and winners:
        title_match = max(winners, key=lambda m: m.round or 0)

    rounds = {}
    for m in winners:
        match_score = score_by_pair.get((m.sleeper_roster_id, m.opponent_sleeper_roster_id))
        pf = match_score.points_for if match_score else None
        pa = match_score.points_against if match_score else None
        rounds.setdefault(m.round, []).append({
            'sleeper_matchup_id': m.sleeper_matchup_id,
            'placement': m.placement,
            'is_championship': title_match is not None and m.sleeper_matchup_id == title_match.sleeper_matchup_id and m.round == title_match.round,
            'winner_roster_id': m.winner_sleeper_roster_id,
            'team': team_blob(m.sleeper_roster_id, pf),
            'opponent': team_blob(m.opponent_sleeper_roster_id, pa),
        })
    bracket = [
        {'round': rnd, 'matchups': rounds[rnd]}
        for rnd in sorted(rounds.keys())
    ]

    # ── Playoff weeks of the champion's run (from their own bracket games) ───
    champ_games = [m for m in winners
                   if champ_roster_id in (m.sleeper_roster_id, m.opponent_sleeper_roster_id)]
    playoff_weeks = set()
    for m in champ_games:
        ms = (score_by_pair.get((m.sleeper_roster_id, m.opponent_sleeper_roster_id))
              or score_by_pair.get((m.opponent_sleeper_roster_id, m.sleeper_roster_id)))
        if ms:
            playoff_weeks.add(ms.week)
    title_week = None
    if title_match is not None:
        tms = (score_by_pair.get((title_match.sleeper_roster_id, title_match.opponent_sleeper_roster_id))
               or score_by_pair.get((title_match.opponent_sleeper_roster_id, title_match.sleeper_roster_id)))
        if tms:
            title_week = tms.week

    # ── Starter stats across the run (joined to Players for names) ──────────
    notable_starters, big_performances, title_game = [], [], None
    if playoff_weeks:
        stat_rows = (db.session.query(PlayerWeeklyStats, Players)
                     .outerjoin(Players, Players.sleeper_id == PlayerWeeklyStats.player_sleeper_id)
                     .filter(PlayerWeeklyStats.year == year,
                             PlayerWeeklyStats.sleeper_roster_id == champ_roster_id,
                             PlayerWeeklyStats.week.in_(playoff_weeks),
                             PlayerWeeklyStats.is_starter.is_(True))
                     .all())

        def player_name(p):
            return f'{p.first_name} {p.last_name}' if p else None

        # Notable starters: total points per player across the run.
        totals = {}
        for stat, player in stat_rows:
            if player is None:
                continue
            key = stat.player_sleeper_id
            agg = totals.setdefault(key, {
                'name': player_name(player),
                'position': player.position,
                'nfl_team': player.nfl_team,
                'total_points': 0.0,
                'games_played': 0,
            })
            agg['total_points'] += float(stat.points or 0)
            agg['games_played'] += 1
        notable_starters = sorted(totals.values(), key=lambda x: x['total_points'], reverse=True)[:5]
        for s in notable_starters:
            s['total_points'] = round(s['total_points'], 1)

        # Big performances: top single-game starter scores during the run.
        # week -> the champion's opponent that week (for the "vs ..." label).
        # Read straight from the champion's Matchups rows (either column) so it's
        # robust to one-sided playoff-week data and bracket/Matchups pairing gaps.
        week_opp = {}
        for m in score_rows:
            if m.week not in playoff_weeks:
                continue
            if m.sleeper_roster_id == champ_roster_id:
                week_opp[m.week] = (team_by_roster.get(m.opponent_sleeper_roster_id) or {}).get('team_name')
            elif m.opponent_sleeper_roster_id == champ_roster_id:
                week_opp.setdefault(m.week, (team_by_roster.get(m.sleeper_roster_id) or {}).get('team_name'))
        perfs = []
        for stat, player in stat_rows:
            if player is None:
                continue
            perfs.append({
                'name': player_name(player),
                'position': player.position,
                'week': stat.week,
                'points': round(float(stat.points or 0), 1),
                'opponent_team_name': week_opp.get(stat.week),
            })
        big_performances = sorted(perfs, key=lambda x: x['points'], reverse=True)[:5]

        # Title-game box score: champion's starters in the title week.
        if title_week is not None:
            starters = sorted(
                ({'name': player_name(player), 'position': player.position,
                  'points': round(float(stat.points or 0), 1)}
                 for stat, player in stat_rows if stat.week == title_week and player is not None),
                key=lambda x: x['points'], reverse=True)
            tms = score_by_pair.get((title_match.sleeper_roster_id, title_match.opponent_sleeper_roster_id)) \
                if title_match else None
            # Orient the score from the champion's perspective.
            if tms and tms.sleeper_roster_id == champ_roster_id:
                pf, pa, opp_roster = tms.points_for, tms.points_against, tms.opponent_sleeper_roster_id
            else:
                alt = score_by_pair.get((champ_roster_id, title_match.opponent_sleeper_roster_id
                                         if title_match.sleeper_roster_id == champ_roster_id
                                         else title_match.sleeper_roster_id)) if title_match else None
                pf = alt.points_for if alt else None
                pa = alt.points_against if alt else None
                opp_roster = alt.opponent_sleeper_roster_id if alt else None
            opp_info = team_by_roster.get(opp_roster) or {}
            title_game = {
                'week': title_week,
                'opponent_team_name': opp_info.get('team_name'),
                'points_for': pf,
                'points_against': pa,
                'starters': starters,
            }

    # ── Franchise / season context ──────────────────────────────────────────
    season_record = TeamRecords.query.filter_by(team_id=champ_team.team_id, year=year).first()
    seed = seed_by_team_id.get(champ_team.team_id)

    return jsonify(
        success=True,
        champion={
            'year': year,
            'team_id': champ_team.team_id,
            'team_name': champ_team.team_name,
            'owners': UsersJSONSchema(many=True).dump(champ_team.owners),
            'season_record': {
                'wins': int(season_record.wins) if season_record else 0,
                'losses': int(season_record.losses) if season_record else 0,
                'points_for': float(season_record.points_for) if season_record else 0.0,
                'points_against': float(season_record.points_against) if season_record else 0.0,
            },
        },
        franchise={'seed': seed, 'championships': champ_team.championships},
        bracket=bracket,
        notable_starters=notable_starters,
        big_performances=big_performances,
        title_game=title_game,
    )

@teams.route('/teams', methods=['GET', 'OPTIONS'])
def get_teams():
    current_year = get_current_year()
    
    teams = Teams.query \
        .join(TeamRecords, Teams.team_id == TeamRecords.team_id) \
        .filter(TeamRecords.year == current_year) \
        .order_by(
            TeamRecords.wins.desc(),
            TeamRecords.points_for.desc()
        ).all()

    return jsonify(success=True, teams=[ team.serialize_list() for team in teams ])

@teams.route('/teams/<int:team_id>', methods=['GET', 'OPTIONS'])
def get_team(team_id):
    team = Teams.query.get(team_id)
    return jsonify(success=True, team=team.serialize())

@teams.route('/teams/<int:team_id>/matchups', methods=['GET', 'OPTIONS'])
def get_team_matchups(team_id):
    # Get team efficiently with error handling
    team = Teams.query.get(team_id)
    if not team:
        return jsonify(success=False, error="Team not found"), 404
    
    current_year = get_current_year()
    
    matchups = Matchups.query \
        .filter_by(sleeper_roster_id=team.sleeper_roster_id, year=current_year) \
        .order_by(Matchups.week) \
        .all()
    
    return jsonify(success=True, matchups=[matchup.serialize() for matchup in matchups])

@teams.route('/teams/<int:team_id>/matchups/fast', methods=['GET', 'OPTIONS'])
def get_team_matchups_fast(team_id):
    """Ultra-fast team matchups using raw SQL for maximum performance"""
    
    current_year = get_current_year()
    
    sql = """
    SELECT 
        m.matchup_id,
        m.year,
        m.week,
        m.sleeper_matchup_id,
        m.sleeper_roster_id,
        m.opponent_sleeper_roster_id,
        m.points_for,
        m.points_against,
        m.completed,
        t2.team_name as opponent_team_name
    FROM Matchups m
    INNER JOIN Teams t1 ON m.sleeper_roster_id = t1.sleeper_roster_id
    LEFT JOIN Teams t2 ON m.opponent_sleeper_roster_id = t2.sleeper_roster_id
    WHERE t1.team_id = :team_id AND m.year = :current_year
    ORDER BY m.week
    """
    
    result = db.session.execute(sql, {'team_id': team_id, 'current_year': current_year})
    matchups_data = []
    
    for row in result:
        matchups_data.append({
            'matchup_id': row[0],
            'year': row[1],
            'week': row[2], 
            'sleeper_matchup_id': row[3],
            'sleeper_roster_id': row[4],
            'opponent_sleeper_roster_id': row[5],
            'points_for': float(row[6]),
            'points_against': float(row[7]),
            'completed': bool(row[8]),
            'opponent_team_name': row[9]
        })
    
    return jsonify(success=True, matchups=matchups_data)

@teams.route('/teams/<int:team_id>/articles', methods=['GET', 'OPTIONS'])
def get_team_articles(team_id):
    team = Teams.query.get(team_id)
    articles = team.articles
    return jsonify(success=True, articles=[ article.serialize() for article in articles ])


