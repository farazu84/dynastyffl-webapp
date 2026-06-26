"""
Tests for the championship endpoints added on this branch.

Coverage
────────
  app.logic.history.champion_roster_by_year()   – champion-per-season derivation
  GET /v1/teams/recent_champions                – last 5 champions + season record
  GET /v1/teams/champions/<year>                – full title run (bracket, run leaders,
                                                  big games, title box score, franchise)

Fixture strategy
────────────────
  • `db` / `client` fixtures from conftest (SQLite in-memory, function-scoped)
  • `make_team` / `make_player` from conftest for Teams/Players
  • Local seed_* helpers below for the tables conftest doesn't cover
    (TeamRecords, PlayoffMatchups, Matchups, PlayerWeeklyStats)

The 2024 scenario (seed_2024_run) wires a 4-team playoff so the derived values are
hand-checkable:

  Standings (regular season) → seeds:  team1=1, team2=2, team3=3, team4=4
  Winners bracket:
    R1 (wk15):  (1) beats (4) 110-90      |  (2) beats (3) 120-100   ← champ semifinal
    R2 (wk16):  CHAMPIONSHIP p=1: (2) beats (1) 140-130  ← champion = roster 2
                3RD PLACE   p=3: (4) beats (3)  95-80
  Champion roster-2 starters (playoff wks 15-16):
    QB 201  wk15 20  wk16 30   (starter)  → run total 50
    RB 202  wk15 25  wk16 10   (starter)  → run total 35
    WR 203  wk16 40            (BENCH)    → excluded from starter aggregates
"""

from tests.conftest import make_team, make_player


# ─────────────────────────────────────────────────────────────────────────────
# Local seed helpers (tables conftest doesn't provide)
# ─────────────────────────────────────────────────────────────────────────────

def seed_team_record(db, team_id, year, wins, losses, points_for, points_against):
    from app.models.team_records import TeamRecords
    r = TeamRecords(team_id=team_id, year=year, wins=wins, losses=losses,
                    points_for=points_for, points_against=points_against)
    db.session.add(r)
    return r


def seed_playoff(db, year, round_, matchup_id, roster, opponent, winner,
                 bracket='winners', loser=None, placement=None):
    from app.models.playoff_matchups import PlayoffMatchups
    m = PlayoffMatchups(
        year=year, round=round_, bracket=bracket, sleeper_matchup_id=matchup_id,
        sleeper_roster_id=roster, opponent_sleeper_roster_id=opponent,
        winner_sleeper_roster_id=winner, loser_sleeper_roster_id=loser,
        placement=placement,
    )
    db.session.add(m)
    return m


def seed_matchup(db, year, week, matchup_id, roster, opponent, points_for, points_against):
    from app.models.matchups import Matchups
    m = Matchups(
        year=year, week=week, sleeper_matchup_id=matchup_id,
        sleeper_roster_id=roster, opponent_sleeper_roster_id=opponent,
        points_for=points_for, points_against=points_against, completed=True,
    )
    db.session.add(m)
    return m


def seed_stat(db, year, week, roster, player_sleeper_id, points, is_starter):
    from app.models.player_weekly_stats import PlayerWeeklyStats
    s = PlayerWeeklyStats(
        year=year, week=week, sleeper_roster_id=roster,
        player_sleeper_id=player_sleeper_id, points=points, is_starter=is_starter,
    )
    db.session.add(s)
    return s


def seed_champion_season(db, year, *, roster, team_id, wins, losses, pf, pa, matchup_id=1):
    """Minimal champion season: one placement=1 championship game + the champ's record."""
    seed_playoff(db, year=year, round_=1, matchup_id=matchup_id,
                 roster=roster, opponent=roster + 1, winner=roster, placement=1)
    seed_team_record(db, team_id=team_id, year=year, wins=wins, losses=losses,
                     points_for=pf, points_against=pa)


def seed_2024_run(db):
    """Seed the full hand-checkable 2024 championship scenario (champion = roster 2)."""
    for i in range(1, 5):
        make_team(db, team_id=i, sleeper_roster_id=i, team_name=f'Team {i}')

    # Champion roster-2 players (201 starter QB, 202 starter RB, 203 bench WR).
    make_player(db, player_id=201, sleeper_id=201, first_name='Star', last_name='QB', position='QB')
    make_player(db, player_id=202, sleeper_id=202, first_name='Big', last_name='RB', position='RB')
    make_player(db, player_id=203, sleeper_id=203, first_name='Bench', last_name='WR', position='WR')

    # Regular-season standings → seeds (wins desc, pf desc): 1,2,3,4
    seed_team_record(db, team_id=1, year=2024, wins=10, losses=3, points_for=1500, points_against=1300)
    seed_team_record(db, team_id=2, year=2024, wins=9,  losses=4, points_for=1450, points_against=1320)
    seed_team_record(db, team_id=3, year=2024, wins=8,  losses=5, points_for=1400, points_against=1350)
    seed_team_record(db, team_id=4, year=2024, wins=7,  losses=6, points_for=1300, points_against=1380)

    # Winners bracket
    seed_playoff(db, year=2024, round_=1, matchup_id=1, roster=1, opponent=4, winner=1)            # semfinal
    seed_playoff(db, year=2024, round_=1, matchup_id=2, roster=2, opponent=3, winner=2)            # champ semifinal
    seed_playoff(db, year=2024, round_=2, matchup_id=3, roster=1, opponent=2, winner=2, placement=1)  # CHAMPIONSHIP
    seed_playoff(db, year=2024, round_=2, matchup_id=4, roster=4, opponent=3, winner=4, placement=3)  # 3rd place

    # Matchups carry scores + the playoff week for each pairing.
    seed_matchup(db, year=2024, week=15, matchup_id=1, roster=1, opponent=4, points_for=110, points_against=90)
    seed_matchup(db, year=2024, week=15, matchup_id=2, roster=2, opponent=3, points_for=120, points_against=100)
    seed_matchup(db, year=2024, week=16, matchup_id=3, roster=1, opponent=2, points_for=130, points_against=140)
    seed_matchup(db, year=2024, week=16, matchup_id=4, roster=4, opponent=3, points_for=95, points_against=80)
    # Champion's own perspective for the title week (orients the box score / opponent label).
    seed_matchup(db, year=2024, week=16, matchup_id=3, roster=2, opponent=1, points_for=140, points_against=130)

    # Champion starter stats across the run (wks 15-16). 203 is a bench-week-16 outlier.
    seed_stat(db, year=2024, week=15, roster=2, player_sleeper_id=201, points=20, is_starter=True)
    seed_stat(db, year=2024, week=16, roster=2, player_sleeper_id=201, points=30, is_starter=True)
    seed_stat(db, year=2024, week=15, roster=2, player_sleeper_id=202, points=25, is_starter=True)
    seed_stat(db, year=2024, week=16, roster=2, player_sleeper_id=202, points=10, is_starter=True)
    seed_stat(db, year=2024, week=16, roster=2, player_sleeper_id=203, points=40, is_starter=False)
    # A non-champion roster stat that must never leak into champion aggregates.
    seed_stat(db, year=2024, week=16, roster=1, player_sleeper_id=201, points=99, is_starter=True)

    db.session.commit()


# ═══════════════════════════════════════════════════════════════════════════
# champion_roster_by_year()
# ═══════════════════════════════════════════════════════════════════════════

class TestChampionRosterByYear:
    def test_picks_placement_one_winner(self, db):
        from app.logic.history import champion_roster_by_year
        # Highest round is round 2 (won by roster 5), but placement==1 game (round 1)
        # was won by roster 7 — the placement marker must win.
        seed_playoff(db, year=2024, round_=2, matchup_id=10, roster=5, opponent=6, winner=5)
        seed_playoff(db, year=2024, round_=1, matchup_id=11, roster=7, opponent=8, winner=7, placement=1)
        db.session.commit()

        assert champion_roster_by_year() == {2024: 7}

    def test_falls_back_to_highest_round_without_placement(self, db):
        from app.logic.history import champion_roster_by_year
        seed_playoff(db, year=2023, round_=1, matchup_id=20, roster=1, opponent=2, winner=1)
        seed_playoff(db, year=2023, round_=2, matchup_id=21, roster=3, opponent=4, winner=3)
        db.session.commit()

        assert champion_roster_by_year() == {2023: 3}

    def test_multiple_seasons_independently(self, db):
        from app.logic.history import champion_roster_by_year
        seed_playoff(db, year=2022, round_=1, matchup_id=30, roster=1, opponent=2, winner=2, placement=1)
        seed_playoff(db, year=2023, round_=1, matchup_id=31, roster=3, opponent=4, winner=4, placement=1)
        db.session.commit()

        assert champion_roster_by_year() == {2022: 2, 2023: 4}

    def test_losers_bracket_ignored(self, db):
        from app.logic.history import champion_roster_by_year
        seed_playoff(db, year=2024, round_=3, matchup_id=40, roster=9, opponent=10, winner=9,
                     bracket='losers', placement=1)
        db.session.commit()

        assert champion_roster_by_year() == {}


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/teams/recent_champions
# ═══════════════════════════════════════════════════════════════════════════

class TestRecentChampions:
    def test_empty_without_playoffs(self, client, db):
        make_team(db, team_id=1, sleeper_roster_id=1)
        db.session.commit()

        r = client.get('/v1/teams/recent_champions')
        assert r.status_code == 200
        data = r.get_json()
        assert data['success'] is True
        assert data['champions'] == []

    def test_returns_record_and_newest_first(self, client, db):
        make_team(db, team_id=1, sleeper_roster_id=1, team_name='Dynasty')
        seed_champion_season(db, 2023, roster=1, team_id=1, wins=8, losses=5, pf=1400, pa=1300, matchup_id=1)
        seed_champion_season(db, 2024, roster=1, team_id=1, wins=11, losses=2, pf=1600, pa=1200, matchup_id=2)
        db.session.commit()

        data = client.get('/v1/teams/recent_champions').get_json()
        assert [c['year'] for c in data['champions']] == [2024, 2023]

        first = data['champions'][0]
        assert first['team_name'] == 'Dynasty'
        assert first['season_record'] == {
            'wins': 11, 'losses': 2, 'points_for': 1600.0, 'points_against': 1200.0,
        }

    def test_limited_to_five_most_recent(self, client, db):
        for offset, year in enumerate(range(2020, 2026)):  # six champion seasons
            make_team(db, team_id=year, sleeper_roster_id=year, team_name=f'Champ {year}')
            seed_champion_season(db, year, roster=year, team_id=year,
                                 wins=10, losses=3, pf=1500, pa=1300, matchup_id=year)
        db.session.commit()

        years = [c['year'] for c in client.get('/v1/teams/recent_champions').get_json()['champions']]
        assert years == [2025, 2024, 2023, 2022, 2021]  # newest five, 2020 dropped


# ═══════════════════════════════════════════════════════════════════════════
# GET /v1/teams/champions/<year>
# ═══════════════════════════════════════════════════════════════════════════

class TestChampionshipRun:
    def test_404_for_non_champion_year(self, client, db):
        make_team(db, team_id=1, sleeper_roster_id=1)
        db.session.commit()

        r = client.get('/v1/teams/champions/2099')
        assert r.status_code == 404
        assert r.get_json()['success'] is False

    def test_champion_and_franchise(self, client, db):
        seed_2024_run(db)
        d = client.get('/v1/teams/champions/2024').get_json()

        assert d['success'] is True
        assert d['champion']['team_name'] == 'Team 2'
        assert d['champion']['season_record'] == {
            'wins': 9, 'losses': 4, 'points_for': 1450.0, 'points_against': 1320.0,
        }
        # Champion was the 2-seed in the regular season.
        assert d['franchise']['seed'] == 2

    def test_bracket_rounds_scores_and_flags(self, client, db):
        seed_2024_run(db)
        d = client.get('/v1/teams/champions/2024').get_json()

        rounds = {r['round']: r['matchups'] for r in d['bracket']}
        assert set(rounds) == {1, 2}

        # Championship game: placement 1, flagged, champion (roster 2) won.
        title = next(m for m in rounds[2] if m['placement'] == 1)
        assert title['is_championship'] is True
        assert title['winner_roster_id'] == 2
        # Scores resolved from Matchups, seeds attached to each side.
        assert title['team']['seed'] == 1 and title['opponent']['seed'] == 2
        assert title['team']['points'] == 130.0 and title['opponent']['points'] == 140.0

        # 3rd-place game present and labelled via placement.
        assert any(m['placement'] == 3 for m in rounds[2])
        # Non-final games carry no placement.
        assert all(m['placement'] is None for m in rounds[1])

    def test_notable_starters_aggregate_excluding_bench(self, client, db):
        seed_2024_run(db)
        d = client.get('/v1/teams/champions/2024').get_json()

        starters = d['notable_starters']
        names = [s['name'] for s in starters]
        # Bench WR (203) excluded; non-champion roster's 201 stat not leaked.
        assert names == ['Star QB', 'Big RB']
        assert starters[0]['total_points'] == 50.0 and starters[0]['games_played'] == 2
        assert starters[1]['total_points'] == 35.0
        assert 'Bench WR' not in names

    def test_big_performances_single_game_with_opponent(self, client, db):
        seed_2024_run(db)
        d = client.get('/v1/teams/champions/2024').get_json()

        perfs = d['big_performances']
        top = perfs[0]
        assert top['name'] == 'Star QB' and top['week'] == 16 and top['points'] == 30.0
        assert top['opponent_team_name'] == 'Team 1'      # champ's wk16 opponent
        # Bench 40-pt game must not appear; all listed are starters.
        assert all(p['name'] != 'Bench WR' for p in perfs)
        # Week-15 performances are tagged with the semifinal opponent.
        wk15 = next(p for p in perfs if p['week'] == 15)
        assert wk15['opponent_team_name'] == 'Team 3'

    def test_title_game_box_score(self, client, db):
        seed_2024_run(db)
        d = client.get('/v1/teams/champions/2024').get_json()

        tg = d['title_game']
        assert tg['week'] == 16
        assert tg['opponent_team_name'] == 'Team 1'
        # Oriented from the champion's perspective (they won 140-130).
        assert tg['points_for'] == 140.0 and tg['points_against'] == 130.0
        # Only champion starters for the title week, sorted by points desc.
        assert [s['name'] for s in tg['starters']] == ['Star QB', 'Big RB']
        assert [s['points'] for s in tg['starters']] == [30.0, 10.0]
