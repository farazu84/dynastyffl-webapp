import requests
import os
import time
import logging
from datetime import datetime, timezone
from app import db
from app.models.transactions import Transactions
from app.models.transaction_players import TransactionPlayers
from app.models.transaction_rosters import TransactionRosters
from app.models.transaction_draft_picks import TransactionDraftPicks
from app.models.transaction_waiver_budget import TransactionWaiverBudget

logger = logging.getLogger(__name__)

# League ID chain for historical backfill (2019-2026)
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


def _epoch_ms_to_datetime(epoch_ms):
    """Convert epoch milliseconds (from Sleeper API) to a datetime object."""
    if epoch_ms is None:
        return None
    return datetime.fromtimestamp(int(epoch_ms) / 1000, tz=timezone.utc)


def _process_transaction(txn_data, year, week, league_id):
    """
    Process a single transaction dict from the Sleeper API.
    Creates the parent Transactions row and all child rows.
    Returns the Transactions object if created, None if skipped (already exists or invalid).
    """
    sleeper_id = txn_data.get('transaction_id')
    if not sleeper_id:
        return None

    # Dedup by sleeper_transaction_id
    existing = Transactions.query.filter_by(sleeper_transaction_id=int(sleeper_id)).first()
    if existing:
        return None

    txn_type = txn_data.get('type')
    if txn_type not in ('trade', 'waiver', 'free_agent'):
        return None

    settings = txn_data.get('settings') or {}

    # Create parent transaction
    transaction = Transactions(
        sleeper_transaction_id=int(sleeper_id),
        year=year,
        week=week,
        type=txn_type,
        status=txn_data.get('status', 'unknown'),
        creator_sleeper_user_id=int(txn_data['creator']) if txn_data.get('creator') else None,
        sleeper_league_id=int(league_id),
        waiver_priority=settings.get('seq'),
        created_at=_epoch_ms_to_datetime(txn_data.get('created')),
        status_updated_at=_epoch_ms_to_datetime(txn_data.get('status_updated')),
    )
    db.session.add(transaction)
    db.session.flush()  # Get transaction_id for child rows

    # Process roster involvement
    roster_ids = txn_data.get('roster_ids') or []
    consenter_ids = txn_data.get('consenter_ids') or []
    for roster_id in roster_ids:
        tr = TransactionRosters(
            transaction_id=transaction.transaction_id,
            sleeper_roster_id=int(roster_id),
            is_consenter=int(roster_id) in consenter_ids,
        )
        db.session.add(tr)

    # Process player adds
    adds = txn_data.get('adds') or {}
    for player_sleeper_id, roster_id in adds.items():
        tp = TransactionPlayers(
            transaction_id=transaction.transaction_id,
            player_sleeper_id=int(player_sleeper_id),
            sleeper_roster_id=int(roster_id),
            action='add',
        )
        db.session.add(tp)

    # Process player drops
    drops = txn_data.get('drops') or {}
    for player_sleeper_id, roster_id in drops.items():
        tp = TransactionPlayers(
            transaction_id=transaction.transaction_id,
            player_sleeper_id=int(player_sleeper_id),
            sleeper_roster_id=int(roster_id),
            action='drop',
        )
        db.session.add(tp)

    # Process draft picks
    draft_picks = txn_data.get('draft_picks') or []
    for pick in draft_picks:
        season = pick.get('season')
        if season is not None:
            season = int(season)
        dp = TransactionDraftPicks(
            transaction_id=transaction.transaction_id,
            season=season,
            round=pick.get('round'),
            roster_id=pick.get('roster_id'),
            owner_id=pick.get('owner_id'),
            previous_owner_id=pick.get('previous_owner_id'),
        )
        db.session.add(dp)

    # Process waiver budget (FAAB)
    waiver_budget = txn_data.get('waiver_budget') or []
    for budget_entry in waiver_budget:
        if isinstance(budget_entry, dict):
            wb = TransactionWaiverBudget(
                transaction_id=transaction.transaction_id,
                sleeper_roster_id=int(budget_entry.get('sender' , budget_entry.get('roster_id', 0))),
                amount=int(budget_entry.get('amount', 0)),
            )
            db.session.add(wb)

    return transaction


def synchronize_transactions():
    """
    Sync transactions for the current week of the current league.
    Called by SyncService during daily full_sync.
    """
    from app.models.league_state import LeagueState

    league_state = LeagueState.query.filter_by(current=True).first()
    if not league_state:
        raise ValueError("No current league state found.")

    league_id = os.getenv('LEAGUE_ID')
    if not league_id:
        raise RuntimeError("LEAGUE_ID environment variable is not set")
    week = league_state.week
    year = league_state.year

    logger.info(f'Fetching transactions for week {week}, year {year}')

    try:
        response = requests.get(
            f'https://api.sleeper.app/v1/league/{league_id}/transactions/{week}'
        )
        response.raise_for_status()
        txn_list = response.json() or []

        added_count = 0
        for txn_data in txn_list:
            result = _process_transaction(txn_data, year, week, league_id)
            if result:
                added_count += 1

        db.session.commit()
        logger.info(f'Transaction sync complete: {added_count} new transactions for week {week}')
        return {'success': True, 'added_count': added_count, 'week': week, 'year': year}

    except requests.RequestException as e:
        logger.error(f'Failed to fetch transactions from Sleeper API: {e}')
        db.session.rollback()
        raise
    except Exception as e:
        logger.error(f'Transaction sync failed: {e}')
        db.session.rollback()
        raise


def backfill_all_transactions():
    """
    Walk all 8 seasons, weeks 0-18, and pull every transaction.
    Designed to be run once from the backfill script.
    Skips any transaction that already exists (idempotent via sleeper_transaction_id).
    Commits per-week and continues on error.
    """
    total_added = 0

    for year, league_id in sorted(LEAGUE_HISTORY.items()):
        logger.info(f'Backfilling transactions for {year} (league {league_id})')

        for week in range(0, 19):
            try:
                response = requests.get(
                    f'https://api.sleeper.app/v1/league/{league_id}/transactions/{week}'
                )
                response.raise_for_status()
                txn_list = response.json() or []

                week_added = 0
                for txn_data in txn_list:
                    result = _process_transaction(txn_data, year, week, league_id)
                    if result:
                        week_added += 1

                db.session.commit()
                total_added += week_added

                if week_added > 0:
                    logger.info(f'  Year {year} Week {week}: {week_added} transactions added')

                # Rate limit protection
                time.sleep(0.3)

            except requests.RequestException as e:
                logger.error(f'  Year {year} Week {week}: API error - {e}')
                db.session.rollback()
                continue
            except Exception as e:
                logger.error(f'  Year {year} Week {week}: Error - {e}')
                db.session.rollback()
                continue

    logger.info(f'Backfill complete: {total_added} total transactions added')
    return {'success': True, 'total_added': total_added}


def backfill_week_zero():
    """
    Backfill only week 0 transactions for all seasons.
    Skips duplicates via sleeper_transaction_id check in _process_transaction.
    """
    total_added = 0

    for year, league_id in sorted(LEAGUE_HISTORY.items()):
        try:
            logger.info(f'Backfilling week 0 for {year} (league {league_id})')
            response = requests.get(
                f'https://api.sleeper.app/v1/league/{league_id}/transactions/0'
            )
            response.raise_for_status()
            txn_list = response.json() or []

            week_added = 0
            for txn_data in txn_list:
                result = _process_transaction(txn_data, year, 0, league_id)
                if result:
                    week_added += 1

            db.session.commit()
            total_added += week_added

            if week_added > 0:
                logger.info(f'  Year {year} Week 0: {week_added} transactions added')
            else:
                logger.info(f'  Year {year} Week 0: no new transactions')

            time.sleep(0.3)

        except requests.RequestException as e:
            logger.error(f'  Year {year} Week 0: API error - {e}')
            db.session.rollback()
            continue
        except Exception as e:
            logger.error(f'  Year {year} Week 0: Error - {e}')
            db.session.rollback()
            continue

    logger.info(f'Week 0 backfill complete: {total_added} total transactions added')
    return {'success': True, 'total_added': total_added}
