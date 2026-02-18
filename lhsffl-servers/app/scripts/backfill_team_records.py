"""
Backfill script for loading all historical team records (2019-present).

For each season in LEAGUE_HISTORY:
  1. GET /v1/league/<league_id>/rosters  -> get end-of-season W/L/pts per roster
  2. Map each roster_id to a Teams row via sleeper_roster_id
  3. Upsert a TeamRecords row for (team_id, year)

Run from the lhsffl-servers directory:
    venv/bin/python -m app.scripts.backfill_team_records
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


def backfill_team_records():
    from app import db
    from app.models.teams import Teams
    from app.models.team_records import TeamRecords

    total_upserted = 0

    for year, league_id in sorted(LEAGUE_HISTORY.items()):
        logger.info(f'--- {year} (league {league_id}) ---')

        try:
            resp = requests.get(f'https://api.sleeper.app/v1/league/{league_id}/rosters')
            resp.raise_for_status()
            rosters = resp.json() or []
            time.sleep(0.3)

            if not rosters:
                logger.warning(f'  No roster data returned')
                continue

            year_upserted = 0

            for roster in rosters:
                roster_id = roster.get('roster_id')
                settings = roster.get('settings') or {}

                team = Teams.query.filter_by(sleeper_roster_id=roster_id).first()
                if not team:
                    logger.warning(f'  No team found for sleeper_roster_id={roster_id}, skipping')
                    continue

                wins = settings.get('wins', 0)
                losses = settings.get('losses', 0)

                fpts = float(settings.get('fpts', 0) or 0)
                fpts_decimal = float(settings.get('fpts_decimal', 0) or 0)
                points_for = fpts + (fpts_decimal / 100.0)

                fpts_against = float(settings.get('fpts_against', 0) or 0)
                fpts_against_decimal = float(settings.get('fpts_against_decimal', 0) or 0)
                points_against = fpts_against + (fpts_against_decimal / 100.0)

                existing = TeamRecords.query.filter_by(
                    team_id=team.team_id,
                    year=year
                ).first()

                if existing:
                    existing.wins = wins
                    existing.losses = losses
                    existing.points_for = points_for
                    existing.points_against = points_against
                    logger.info(f'  Updated {team.team_name} ({year}): {wins}-{losses}, PF {points_for:.2f}')
                else:
                    new_record = TeamRecords(
                        team_id=team.team_id,
                        year=year,
                        wins=wins,
                        losses=losses,
                        points_for=points_for,
                        points_against=points_against,
                    )
                    db.session.add(new_record)
                    logger.info(f'  Inserted {team.team_name} ({year}): {wins}-{losses}, PF {points_for:.2f}')

                year_upserted += 1

            db.session.commit()
            total_upserted += year_upserted
            logger.info(f'  {year} total: {year_upserted} records upserted')

        except requests.RequestException as e:
            logger.error(f'  {year}: API error - {e}')
            db.session.rollback()
            continue
        except Exception as e:
            logger.error(f'  {year}: error - {e}')
            db.session.rollback()
            continue

    logger.info(f'Team records backfill complete: {total_upserted} total records upserted')
    return {'success': True, 'total_upserted': total_upserted}


def main():
    from app import create_app
    from config import DevConfig

    app = create_app(DevConfig)

    with app.app_context():
        result = backfill_team_records()
        logger.info(f'Result: {result}')


if __name__ == '__main__':
    main()
