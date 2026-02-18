"""
Backfill script for loading all historical matchups (2019-present).

For each season in LEAGUE_HISTORY:
  1. GET /v1/league/<league_id>/matchups/<week>  -> get matchup pairs per week
  2. Insert Matchups rows (two per matchup: one per team)
  3. Stop a season's week loop when the API returns an empty response

Idempotent: skips rows where (year, week, sleeper_roster_id) already exists.

Run from the lhsffl-servers directory:
    venv/bin/python -m app.scripts.backfill_matchups
"""
import sys
import os
import time
import logging
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from dotenv import load_dotenv
flaskenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.flaskenv')
load_dotenv(flaskenv_path)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LEAGUE_HISTORY = {
    2019: '419666295387082752',
    2020: '516385651688570880',
    2021: '650601235019292672',
    2022: '785954136989769728',
    2023: '932976884349030400',
    2024: '1063040492125937664',
    2025: '1195252934627844096',
    2026: '1328498202462126080',
}

CURRENT_YEAR = 2026
MAX_WEEKS = 18


def backfill_matchups():
    from app import db
    from app.models.matchups import Matchups

    total_added = 0

    for year, league_id in sorted(LEAGUE_HISTORY.items()):
        logger.info(f'--- {year} (league {league_id}) ---')
        year_added = 0

        for week in range(1, MAX_WEEKS + 1):
            try:
                resp = requests.get(
                    f'https://api.sleeper.app/v1/league/{league_id}/matchups/{week}'
                )
                resp.raise_for_status()
                raw = resp.json() or []
                time.sleep(0.3)

                # Filter out bye-week entries (matchup_id is None)
                active = [m for m in raw if m.get('matchup_id') is not None]

                if not active:
                    logger.info(f'  Week {week}: empty response, stopping season')
                    break

                # Build lookup: matchup_id -> list of roster entries
                matchup_groups = {}
                for entry in active:
                    mid = entry['matchup_id']
                    matchup_groups.setdefault(mid, []).append(entry)

                week_added = 0
                # Past seasons are fully completed; current season rows start incomplete
                is_completed = year < CURRENT_YEAR

                for mid, entries in matchup_groups.items():
                    if len(entries) != 2:
                        logger.warning(f'  Week {week}, matchup {mid}: expected 2 teams, got {len(entries)}, skipping')
                        continue

                    e1, e2 = entries

                    for my_entry, opp_entry in [(e1, e2), (e2, e1)]:
                        my_rid = my_entry['roster_id']
                        opp_rid = opp_entry['roster_id']

                        # Idempotency check
                        existing = Matchups.query.filter_by(
                            year=year,
                            week=week,
                            sleeper_roster_id=my_rid
                        ).first()
                        if existing:
                            continue

                        new_row = Matchups(
                            year=year,
                            week=week,
                            sleeper_matchup_id=mid,
                            sleeper_roster_id=my_rid,
                            opponent_sleeper_roster_id=opp_rid,
                            points_for=float(my_entry.get('points') or 0),
                            points_against=float(opp_entry.get('points') or 0),
                            completed=is_completed,
                        )
                        db.session.add(new_row)
                        week_added += 1

                db.session.commit()
                year_added += week_added
                logger.info(f'  Week {week}: {week_added} rows added')

            except requests.RequestException as e:
                logger.error(f'  Week {week}: API error - {e}')
                db.session.rollback()
                continue
            except Exception as e:
                logger.error(f'  Week {week}: error - {e}')
                db.session.rollback()
                continue

        total_added += year_added
        logger.info(f'  {year} total: {year_added} rows added')

    logger.info(f'Matchup backfill complete: {total_added} total rows added')
    return {'success': True, 'total_added': total_added}


def main():
    from app import create_app
    from config import DevConfig

    app = create_app(DevConfig)

    with app.app_context():
        result = backfill_matchups()
        logger.info(f'Result: {result}')


if __name__ == '__main__':
    main()
