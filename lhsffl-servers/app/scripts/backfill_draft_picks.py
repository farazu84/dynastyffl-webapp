"""
Backfill script for loading all historical draft picks (2019-2026).

For each season in LEAGUE_HISTORY:
  1. GET /v1/league/<league_id>/drafts  -> find the draft ID
  2. GET /v1/draft/<draft_id>/picks     -> get every pick with the player selected

Run from the lhsffl-servers directory:
    venv/bin/python -m app.scripts.backfill_draft_picks
"""
import sys
import os
import time
import logging
import requests

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Load environment variables from .flaskenv
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

# The 2019 startup draft ID — all other drafts are rookie drafts
STARTUP_DRAFT_ID = 424730242209304576


def backfill_draft_picks():
    from app import db
    from app.models.draft_picks import DraftPicks

    total_added = 0

    for year, league_id in sorted(LEAGUE_HISTORY.items()):
        logger.info(f'Fetching drafts for {year} (league {league_id})')

        try:
            # Step 1: Get draft IDs for this league
            resp = requests.get(f'https://api.sleeper.app/v1/league/{league_id}/drafts')
            resp.raise_for_status()
            drafts = resp.json() or []
            time.sleep(0.3)

            if not drafts:
                logger.info(f'  No drafts found for {year}')
                continue

            for draft in drafts:
                draft_id = draft.get('draft_id')
                if not draft_id:
                    continue

                # Skip if we already have picks for this draft
                existing = DraftPicks.query.filter_by(sleeper_draft_id=int(draft_id)).first()
                if existing:
                    logger.info(f'  Draft {draft_id} already backfilled, skipping')
                    continue

                # Step 2: Get draft details for slot_to_roster_id mapping
                detail_resp = requests.get(f'https://api.sleeper.app/v1/draft/{draft_id}')
                detail_resp.raise_for_status()
                slot_to_roster = detail_resp.json().get('slot_to_roster_id', {})
                slot_to_original = {}
                for slot, rid in slot_to_roster.items():
                    if slot and rid:
                        slot_to_original[int(slot)] = int(rid)
                time.sleep(0.3)

                # Step 3: Get all picks for this draft
                picks_resp = requests.get(f'https://api.sleeper.app/v1/draft/{draft_id}/picks')
                picks_resp.raise_for_status()
                picks = picks_resp.json() or []
                time.sleep(0.3)

                draft_type = 'startup' if int(draft_id) == STARTUP_DRAFT_ID else 'rookie'

                draft_added = 0
                for pick_data in picks:
                    player_id = pick_data.get('player_id')
                    if not player_id:
                        continue

                    draft_slot = pick_data.get('draft_slot')
                    dp = DraftPicks(
                        season=year,
                        round=pick_data.get('round'),
                        pick_no=pick_data.get('pick_no'),
                        draft_slot=draft_slot,
                        drafting_roster_id=pick_data.get('roster_id'),
                        original_roster_id=slot_to_original.get(draft_slot),
                        player_sleeper_id=int(player_id),
                        sleeper_draft_id=int(draft_id),
                        type=draft_type,
                    )
                    db.session.add(dp)
                    draft_added += 1

                db.session.commit()
                total_added += draft_added
                logger.info(f'  {year} draft {draft_id}: {draft_added} picks added')

        except requests.RequestException as e:
            logger.error(f'  {year}: API error - {e}')
            db.session.rollback()
            continue
        except Exception as e:
            logger.error(f'  {year}: Error - {e}')
            db.session.rollback()
            continue

    logger.info(f'Backfill complete: {total_added} total draft picks added')
    return {'success': True, 'total_added': total_added}


def main():
    from app import create_app
    from config import DevConfig

    app = create_app(DevConfig)

    with app.app_context():
        result = backfill_draft_picks()
        logger.info(f'Result: {result}')


if __name__ == '__main__':
    main()
