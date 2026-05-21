import requests
import csv
import io
import os
from app import db
from app.models.players import Players
from app.models.nfl_draft_data import NFLDraftData
from app.models.player_game_logs import PlayerGameLogs

NFLVERSE_BASE_URL = 'https://github.com/nflverse/nflverse-data/releases/download'


def _fetch_csv(release, filename):
    """
    Download a CSV file from nflverse GitHub releases.
    Uses GITHUB_TOKEN env var if available to avoid rate limits.
    """
    url = f'{NFLVERSE_BASE_URL}/{release}/{filename}.csv'
    headers = {}
    github_token = os.getenv('GITHUB_TOKEN')
    if github_token:
        headers['Authorization'] = f'token {github_token}'

    print(f"Fetching nflverse data from: {url}")
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    return list(csv.DictReader(io.StringIO(response.text)))


def _safe_int(val):
    if val is None or str(val).strip() == '':
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val):
    if val is None or str(val).strip() == '':
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_bool(val):
    if val is None or str(val).strip() == '':
        return False
    return str(val).strip().upper() in ('TRUE', '1', 'YES', 'T')


def _known_gsis_ids():
    """Return the set of gsis_ids currently in the Players table."""
    rows = (
        Players.query
        .with_entities(Players.gsis_id)
        .filter(Players.gsis_id.isnot(None))
        .all()
    )
    return {r.gsis_id for r in rows}


def backfill_player_ids():
    """
    Backfill missing gsis_id and pfr_id on the Players table using nflverse
    players and ff_playerids datasets, joined on sleeper_id.

    Strategy:
      1. Build a sleeper_id → {gsis_id, pfr_id} lookup from ff_playerids
         (most comprehensive for fantasy players).
      2. Fill gaps using the nflverse players dataset as a secondary source.
      3. Update any Players row missing gsis_id or pfr_id.

    This must run before synchronize_nfl_draft_data() and
    synchronize_player_game_logs() so those syncs can match more players.

    Sources: nflverse load_ff_playerids() + load_players() — CC BY 4.0
    """
    try:
        # Build lookup: sleeper_id (str) → {gsis_id, pfr_id}
        lookup = {}

        # Source 1: ff_playerids — most complete for fantasy-relevant players
        ff_rows = _fetch_csv('ff_playerids', 'ff_playerids')
        print(f"Downloaded {len(ff_rows)} ff_playerids rows")
        for row in ff_rows:
            sleeper = (row.get('sleeper_id') or '').strip()
            if not sleeper:
                continue
            gsis = (row.get('gsis_id') or '').strip() or None
            pfr  = (row.get('pfr_id') or '').strip() or None
            if gsis or pfr:
                lookup[sleeper] = {'gsis_id': gsis, 'pfr_id': pfr}

        # Source 2: nflverse players — fill any gaps left by ff_playerids
        player_rows = _fetch_csv('players', 'players')
        print(f"Downloaded {len(player_rows)} players rows")
        for row in player_rows:
            sleeper = (row.get('sleeper_id') or '').strip()
            if not sleeper:
                continue
            gsis = (row.get('gsis_id') or '').strip() or None
            pfr  = (row.get('pfr_id') or '').strip() or None
            if sleeper not in lookup:
                if gsis or pfr:
                    lookup[sleeper] = {'gsis_id': gsis, 'pfr_id': pfr}
            else:
                # Fill individual gaps without overwriting existing values
                if not lookup[sleeper].get('gsis_id') and gsis:
                    lookup[sleeper]['gsis_id'] = gsis
                if not lookup[sleeper].get('pfr_id') and pfr:
                    lookup[sleeper]['pfr_id'] = pfr

        print(f"Built ID lookup with {len(lookup)} sleeper_id entries")

        # Update Players that are missing gsis_id or pfr_id
        players_to_update = Players.query.filter(
            db.or_(Players.gsis_id.is_(None), Players.pfr_id.is_(None))
        ).all()

        updated = 0
        not_found = 0

        for player in players_to_update:
            sleeper_key = str(player.sleeper_id)
            ids = lookup.get(sleeper_key)
            if not ids:
                not_found += 1
                continue

            changed = False
            if not player.gsis_id and ids.get('gsis_id'):
                player.gsis_id = ids['gsis_id']
                changed = True
            if not player.pfr_id and ids.get('pfr_id'):
                player.pfr_id = ids['pfr_id']
                changed = True

            if changed:
                updated += 1

        db.session.commit()
        print(f"Player ID backfill complete: {updated} updated, {not_found} not found in nflverse")
        return {'success': True, 'updated': updated, 'not_found': not_found}

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch nflverse ID data: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        print(f"ERROR: Player ID backfill failed: {e}")
        db.session.rollback()
        raise


def synchronize_nfl_draft_data():
    """
    Fetch NFL draft pick history from nflverse and upsert into NFLDraftData.
    Only processes players whose gsis_id exists in the Players table.
    One row per player — safe to re-run (upsert).

    Source: nflverse load_draft_picks() — CC BY 4.0
    """
    try:
        rows = _fetch_csv('draft_picks', 'draft_picks')
        print(f"Downloaded {len(rows)} draft pick rows from nflverse")

        known_ids = _known_gsis_ids()
        upserted = 0
        skipped = 0

        for row in rows:
            gsis_id = (row.get('gsis_id') or '').strip()
            if not gsis_id or gsis_id not in known_ids:
                skipped += 1
                continue

            values = {
                'nfl_draft_season': _safe_int(row.get('season')),
                'round':            _safe_int(row.get('round')),
                'pick':             _safe_int(row.get('pick')),
                'drafting_team':    (row.get('team') or '')[:8] or None,
                'age_at_draft':     _safe_int(row.get('age')),
                'allpro':           _safe_int(row.get('allpro')) or 0,
                'probowls':         _safe_int(row.get('probowls')) or 0,
                'seasons_started':  _safe_int(row.get('seasons_started')) or 0,
                'career_av':        _safe_int(row.get('car_av')),
                'weighted_av':      _safe_int(row.get('w_av')),
                'hof':              _safe_bool(row.get('hof')),
            }

            # Skip rows missing required fields
            if not values['nfl_draft_season'] or not values['round'] or not values['pick']:
                skipped += 1
                continue

            existing = NFLDraftData.query.filter_by(gsis_id=gsis_id).first()
            if existing:
                for k, v in values.items():
                    setattr(existing, k, v)
            else:
                db.session.add(NFLDraftData(gsis_id=gsis_id, **values))

            upserted += 1

        db.session.commit()
        print(f"NFL draft sync complete: {upserted} upserted, {skipped} skipped (no gsis_id match)")
        return {'success': True, 'upserted': upserted, 'skipped': skipped}

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch nflverse draft data: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        print(f"ERROR: NFL draft sync failed: {e}")
        db.session.rollback()
        raise


def synchronize_player_game_logs(season=None):
    """
    Fetch ff_opportunity data from nflverse and upsert into PlayerGameLogs.
    Only processes players whose gsis_id exists in the Players table.

    ff_opportunity is play-level — deduplicates to one row per player per week
    using the pre-aggregated game-level stat columns included in each play row.

    Args:
        season: Optional int year to fetch a specific season (e.g. 2024).
                Defaults to the current/most recent season file.

    Source: nflverse load_ff_opportunity() — CC BY 4.0
    """
    try:
        filename = f'ff_opportunity_{season}' if season else 'ff_opportunity'
        rows = _fetch_csv('ff_opportunity', filename)
        print(f"Downloaded {len(rows)} ff_opportunity rows from nflverse")

        known_ids = _known_gsis_ids()

        # Deduplicate to one row per (gsis_id, season, week).
        # The player-level aggregated stat columns (rec_attempt, rush_yards_gained,
        # total_fantasy_points, etc.) are game totals repeated on every play row
        # for that player, so taking the first occurrence is correct.
        seen = {}
        for row in rows:
            gsis_id = (row.get('player_id') or '').strip()
            if not gsis_id or gsis_id not in known_ids:
                continue
            s = _safe_int(row.get('season'))
            w = _safe_int(row.get('week'))
            if s is None or w is None:
                continue
            key = (gsis_id, s, w)
            if key not in seen:
                seen[key] = row

        print(f"Unique player-week combinations after dedup: {len(seen)}")

        upserted = 0
        for (gsis_id, s, w), row in seen.items():
            values = {
                'team':                     (row.get('posteam') or '')[:8] or None,
                'targets':                  _safe_int(row.get('rec_attempt')),
                'receptions':               _safe_int(row.get('receptions')),
                'rec_air_yards':            _safe_float(row.get('rec_air_yards')),
                'rec_yards':                _safe_float(row.get('rec_yards_gained')),
                'rec_touchdowns':           _safe_int(row.get('rec_touchdown')),
                'rush_attempts':            _safe_int(row.get('rush_attempt')),
                'rush_yards':               _safe_float(row.get('rush_yards_gained')),
                'rush_touchdowns':          _safe_int(row.get('rush_touchdown')),
                'pass_touchdowns':          _safe_int(row.get('pass_touchdown')),
                'fantasy_points_actual':    _safe_float(row.get('total_fantasy_points')),
                'fantasy_points_expected':  _safe_float(row.get('total_fantasy_points_exp')),
                'fantasy_points_diff':      _safe_float(row.get('total_fantasy_points_diff')),
                'rec_first_downs':          _safe_int(row.get('rec_first_down')),
                'rush_first_downs':         _safe_int(row.get('rush_first_down')),
            }

            existing = PlayerGameLogs.query.filter_by(
                gsis_id=gsis_id, season=s, week=w
            ).first()

            if existing:
                for k, v in values.items():
                    setattr(existing, k, v)
            else:
                db.session.add(PlayerGameLogs(gsis_id=gsis_id, season=s, week=w, **values))

            upserted += 1

            if upserted % 500 == 0:
                db.session.flush()
                print(f"Flushed {upserted} game log rows...")

        db.session.commit()
        print(f"Player game logs sync complete: {upserted} upserted")
        return {'success': True, 'upserted': upserted}

    except requests.RequestException as e:
        print(f"ERROR: Failed to fetch nflverse ff_opportunity data: {e}")
        db.session.rollback()
        raise
    except Exception as e:
        print(f"ERROR: Player game logs sync failed: {e}")
        db.session.rollback()
        raise
