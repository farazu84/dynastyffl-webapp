"""
Historical data backfills from the Sleeper API.

Covers the data the live weekly sync never reaches:
  * Playoff brackets (winners + losers)        -> PlayoffMatchups
  * Per-player weekly league-scored points     -> PlayerWeeklyStats
  * Matchup rows for every season/week         -> Matchups (the live sync only UPDATEs)

Plus derivation helpers that need no new storage:
  * recompute_championships()  -> Teams.championships from PlayoffMatchups
  * current_pick_owners()      -> future draft-pick ownership from TransactionDraftPicks

All writes use MySQL `INSERT ... ON DUPLICATE KEY UPDATE` against the natural-key
UNIQUE constraints, so every backfill is idempotent and safe to re-run (the database
itself rejects duplicates). Functions accept an optional `year` to scope to one season.
"""
import time
import logging

import requests
from sqlalchemy import text

from app import db
from app.league_history import LEAGUE_HISTORY, league_id_for
from app.models.teams import Teams
from app.models.draft_picks import DraftPicks
from app.models.transactions import Transactions
from app.models.transaction_draft_picks import TransactionDraftPicks

logger = logging.getLogger(__name__)

SLEEPER_BASE = 'https://api.sleeper.app/v1'
RATE_LIMIT_SECONDS = 0.3
MAX_WEEK = 18  # regular season + playoffs


def _seasons(year=None):
    """Resolve the seasons to process: one if `year` given, else all known seasons."""
    if year is not None:
        year = int(year)
        if year not in LEAGUE_HISTORY:
            raise ValueError(f'Unknown season {year}; not in LEAGUE_HISTORY')
        return [year]
    return sorted(LEAGUE_HISTORY.keys())


def _roster_or_none(value):
    """Bracket t1/t2 can be an int roster_id or a {'w'/'l': match} reference. Keep ints only."""
    return int(value) if isinstance(value, int) else None


# ---------------------------------------------------------------------------
# Playoff brackets
# ---------------------------------------------------------------------------

_PLAYOFF_UPSERT = text("""
    INSERT INTO PlayoffMatchups
        (year, round, bracket, sleeper_matchup_id, sleeper_roster_id,
         opponent_sleeper_roster_id, winner_sleeper_roster_id,
         loser_sleeper_roster_id, placement)
    VALUES
        (:year, :round, :bracket, :sleeper_matchup_id, :sleeper_roster_id,
         :opponent_sleeper_roster_id, :winner_sleeper_roster_id,
         :loser_sleeper_roster_id, :placement)
    ON DUPLICATE KEY UPDATE
        round = VALUES(round),
        sleeper_roster_id = VALUES(sleeper_roster_id),
        opponent_sleeper_roster_id = VALUES(opponent_sleeper_roster_id),
        winner_sleeper_roster_id = VALUES(winner_sleeper_roster_id),
        loser_sleeper_roster_id = VALUES(loser_sleeper_roster_id),
        placement = VALUES(placement)
""")


def _backfill_bracket(year, league_id, bracket):
    """Fetch one bracket ('winners'|'losers') for a season and upsert its matches."""
    resp = requests.get(f'{SLEEPER_BASE}/league/{league_id}/{bracket}_bracket')
    resp.raise_for_status()
    matches = resp.json() or []
    time.sleep(RATE_LIMIT_SECONDS)

    added = 0
    for match in matches:
        match_id = match.get('m')
        if match_id is None:
            continue
        db.session.execute(_PLAYOFF_UPSERT, {
            'year': year,
            'round': match.get('r') or 0,
            'bracket': bracket,
            'sleeper_matchup_id': match_id,
            'sleeper_roster_id': _roster_or_none(match.get('t1')),
            'opponent_sleeper_roster_id': _roster_or_none(match.get('t2')),
            'winner_sleeper_roster_id': _roster_or_none(match.get('w')),
            'loser_sleeper_roster_id': _roster_or_none(match.get('l')),
            'placement': match.get('p'),
        })
        added += 1
    return added


def backfill_playoffs(year=None):
    """Backfill winners + losers brackets for all (or one) season, then recompute rings."""
    seasons = _seasons(year)
    total = 0
    started = time.time()
    logger.info(f'[playoffs] starting backfill — {len(seasons)} season(s): {seasons}')

    for season_idx, season in enumerate(seasons, start=1):
        league_id = league_id_for(season)
        try:
            winners = _backfill_bracket(season, league_id, 'winners')
            losers = _backfill_bracket(season, league_id, 'losers')
            db.session.commit()
            total += winners + losers
            logger.info(f'[playoffs] ({season_idx}/{len(seasons)}) season {season} — '
                        f'winners +{winners}, losers +{losers} (total {total})')
        except requests.RequestException as e:
            logger.error(f'[playoffs] {season}: API error - {e}')
            db.session.rollback()
            continue
        except Exception as e:
            logger.error(f'[playoffs] {season}: error - {e}')
            db.session.rollback()
            continue

    logger.info('[playoffs] recomputing championships from brackets...')
    champs = recompute_championships()
    logger.info(f'[playoffs] backfill complete — {total} bracket matches, '
                f'{len(champs)} championship season(s) in {time.time() - started:.1f}s')
    return {'success': True, 'matches_upserted': total, 'championship_seasons': len(champs)}


def champion_roster_by_year():
    """Return {season: champion_sleeper_roster_id} derived from PlayoffMatchups winners brackets.

    Champion per season: the championship game (placement == 1) winner; if a season's
    bracket has no placement marker, fall back to the winner of its highest round.
    """
    from app.models.playoff_matchups import PlayoffMatchups

    champ_roster_by_year = {}
    winners = (PlayoffMatchups.query
               .filter_by(bracket='winners')
               .filter(PlayoffMatchups.winner_sleeper_roster_id.isnot(None))
               .all())

    by_year = {}
    for m in winners:
        by_year.setdefault(m.year, []).append(m)

    for season, matches in by_year.items():
        champ_game = next((m for m in matches if m.placement == 1), None)
        if champ_game is None:
            champ_game = max(matches, key=lambda m: m.round or 0)
        champ_roster_by_year[season] = champ_game.winner_sleeper_roster_id

    return champ_roster_by_year


def recompute_championships():
    """Derive Teams.championships from PlayoffMatchups winners brackets (overwrites prior counts)."""
    champ_roster_by_year = champion_roster_by_year()

    # Tally per roster, map to teams, write counts.
    counts = {}
    for roster_id in champ_roster_by_year.values():
        counts[roster_id] = counts.get(roster_id, 0) + 1

    teams = Teams.query.all()
    for team in teams:
        team.championships = counts.get(team.sleeper_roster_id, 0)

    db.session.commit()
    logger.info(f'Recomputed championships for {len(champ_roster_by_year)} seasons')
    return champ_roster_by_year


# ---------------------------------------------------------------------------
# Matchups + per-player weekly stats
# ---------------------------------------------------------------------------

_MATCHUP_UPSERT = text("""
    INSERT INTO Matchups
        (year, week, sleeper_matchup_id, sleeper_roster_id,
         opponent_sleeper_roster_id, points_for, points_against, completed)
    VALUES
        (:year, :week, :sleeper_matchup_id, :sleeper_roster_id,
         :opponent_sleeper_roster_id, :points_for, :points_against, :completed)
    ON DUPLICATE KEY UPDATE
        sleeper_matchup_id = VALUES(sleeper_matchup_id),
        opponent_sleeper_roster_id = VALUES(opponent_sleeper_roster_id),
        points_for = VALUES(points_for),
        points_against = VALUES(points_against),
        completed = VALUES(completed)
""")

_PLAYER_STAT_UPSERT = text("""
    INSERT INTO PlayerWeeklyStats
        (year, week, sleeper_roster_id, player_sleeper_id, points, is_starter)
    VALUES
        (:year, :week, :sleeper_roster_id, :player_sleeper_id, :points, :is_starter)
    ON DUPLICATE KEY UPDATE
        points = VALUES(points),
        is_starter = VALUES(is_starter)
""")


def _upsert_week_matchups(year, week, entries):
    """Upsert Matchups rows (head-to-head + points) from one week's /matchups response."""
    added = 0

    # Group by Sleeper matchup_id to pair opponents.
    groups = {}
    for entry in entries:
        groups.setdefault(entry.get('matchup_id'), []).append(entry)

    for matchup_id, group in groups.items():
        # matchup_id may be None (consolation) and a group may be a bye (len 1) — skip those.
        if matchup_id is None or len(group) != 2:
            continue
        for i, entry in enumerate(group):
            roster_id = entry.get('roster_id')
            if roster_id is None:
                continue
            opponent = group[1 - i]
            points_for = float(entry.get('points') or 0)
            points_against = float(opponent.get('points') or 0)
            db.session.execute(_MATCHUP_UPSERT, {
                'year': year,
                'week': week,
                'sleeper_matchup_id': matchup_id,
                'sleeper_roster_id': roster_id,
                'opponent_sleeper_roster_id': opponent.get('roster_id'),
                'points_for': points_for,
                'points_against': points_against,
                'completed': points_for > 0 or points_against > 0,
            })
            added += 1

    return added


def _upsert_week_player_stats(year, week, entries):
    """Upsert PlayerWeeklyStats (starters + bench, league-scored points) from a week's response."""
    added = 0
    for entry in entries:
        roster_id = entry.get('roster_id')
        if roster_id is None:
            continue
        players_points = entry.get('players_points') or {}
        starters = set(str(s) for s in (entry.get('starters') or []))
        for player_id, points in players_points.items():
            db.session.execute(_PLAYER_STAT_UPSERT, {
                'year': year,
                'week': week,
                'sleeper_roster_id': roster_id,
                'player_sleeper_id': int(player_id),
                'points': float(points or 0),
                'is_starter': str(player_id) in starters,
            })
            added += 1
    return added


def _backfill_weeks(year, label, upsert_week):
    """
    Shared per-season/per-week loop: fetch each /matchups/{week} once and apply
    `upsert_week(season, week, entries) -> count`. Used by both the matchups and
    player-stats backfills so they can run fully independently of each other.

    Emits server-side progress logging (per season, per week, running totals) so
    a long backfill can be followed live in the server logs.
    """
    seasons = _seasons(year)
    total = 0
    started = time.time()
    logger.info(f'[{label}] starting backfill — {len(seasons)} season(s): {seasons}')

    for season_idx, season in enumerate(seasons, start=1):
        league_id = league_id_for(season)
        season_total = 0
        season_started = time.time()
        logger.info(f'[{label}] ({season_idx}/{len(seasons)}) season {season} — starting (league {league_id})')

        for week in range(1, MAX_WEEK + 1):
            try:
                resp = requests.get(f'{SLEEPER_BASE}/league/{league_id}/matchups/{week}')
                resp.raise_for_status()
                entries = resp.json() or []
                time.sleep(RATE_LIMIT_SECONDS)

                if not entries:
                    continue

                added = upsert_week(season, week, entries)
                db.session.commit()
                season_total += added
                total += added
                logger.info(f'[{label}] {season} W{week:>2}: +{added} (season {season_total}, total {total})')
            except requests.RequestException as e:
                logger.error(f'[{label}] {season} W{week}: API error - {e}')
                db.session.rollback()
                continue
            except Exception as e:
                logger.error(f'[{label}] {season} W{week}: error - {e}')
                db.session.rollback()
                continue

        logger.info(f'[{label}] ({season_idx}/{len(seasons)}) season {season} done — '
                    f'{season_total} rows in {time.time() - season_started:.1f}s')

    logger.info(f'[{label}] backfill complete — {total} rows across {len(seasons)} season(s) '
                f'in {time.time() - started:.1f}s')
    return total


def backfill_matchups(year=None):
    """Create/upsert Matchups rows for all (or one) season — independent of player stats."""
    total = _backfill_weeks(year, 'matchups', _upsert_week_matchups)
    return {'success': True, 'matchups_upserted': total}


def backfill_player_stats(year=None):
    """Upsert per-player weekly stats for all (or one) season — independent of matchups."""
    total = _backfill_weeks(year, 'player stats', _upsert_week_player_stats)
    return {'success': True, 'player_weeks_upserted': total}


def sync_current_week_player_stats():
    """Live sync: upsert PlayerWeeklyStats for the current week (matchup points handled separately)."""
    import os
    from app.league_state_manager import get_current_year, get_current_week

    year = get_current_year()
    week = get_current_week()
    league_id = league_id_for(year) or os.environ.get('LEAGUE_ID')
    if not league_id:
        raise RuntimeError('No league_id available for current player-stats sync')

    resp = requests.get(f'{SLEEPER_BASE}/league/{league_id}/matchups/{week}')
    resp.raise_for_status()
    entries = resp.json() or []

    s_added = _upsert_week_player_stats(year, week, entries)
    db.session.commit()
    return {'success': True, 'year': year, 'week': week, 'player_weeks_upserted': s_added}


# ---------------------------------------------------------------------------
# Draft-pick ownership (derived; no storage)
# ---------------------------------------------------------------------------

def _rookie_draft_rounds():
    """Infer how many rounds a rookie draft has from the most recent rookie draft."""
    latest = (DraftPicks.query
              .filter_by(type='rookie')
              .order_by(DraftPicks.season.desc(), DraftPicks.round.desc())
              .first())
    return latest.round if latest else 4  # sensible dynasty default


def current_pick_owners(seasons=None):
    """
    Derive who currently owns each future draft pick — the same "defaults + overlay"
    model Sleeper uses. Untraded picks resolve to their originating roster.

    Returns a list of dicts: {season, round, original_roster_id, current_owner_roster_id}.
    """
    from app.league_state_manager import get_current_year

    if seasons is None:
        current = get_current_year()
        seasons = [current, current + 1, current + 2]

    rounds = _rookie_draft_rounds()
    roster_ids = [t.sleeper_roster_id for t in Teams.query.all()]

    # 1. Defaults: every roster owns its own pick in every (season, round).
    ownership = {}
    for season in seasons:
        for rnd in range(1, rounds + 1):
            for roster_id in roster_ids:
                ownership[(season, rnd, roster_id)] = roster_id

    # 2. Overlay: latest traded move per (season, round, original roster) wins.
    moves = (db.session.query(TransactionDraftPicks, Transactions.created_at)
             .join(Transactions, TransactionDraftPicks.transaction_id == Transactions.transaction_id)
             .filter(TransactionDraftPicks.season.in_(seasons))
             .order_by(Transactions.created_at.asc())
             .all())
    for pick, _created in moves:  # ascending order -> last write wins
        key = (pick.season, pick.round, pick.roster_id)
        if key in ownership and pick.owner_id is not None:
            ownership[key] = pick.owner_id

    return [
        {
            'season': season,
            'round': rnd,
            'original_roster_id': original_roster_id,
            'current_owner_roster_id': current_owner,
        }
        for (season, rnd, original_roster_id), current_owner in sorted(ownership.items())
    ]
