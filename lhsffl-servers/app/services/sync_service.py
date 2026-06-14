import logging
import threading
from datetime import datetime
from app import db
from app.models.sync_status import SyncStatus
from app.logic.league import synchronize_teams, set_league_state, synchronize_matchups, synchronize_players
from app.logic.transactions import synchronize_transactions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Guards a single long-running backfill at a time (also keeps it from racing the scheduler).
_backfill_lock = threading.Lock()
_backfill_state = {'running': False, 'dataset': None, 'started_at': None}


class SyncService:
    """
    Centralized service for managing all Sleeper API synchronization operations.
    Tracks sync status and provides comprehensive error handling.
    """

    SYNC_ITEMS = {
        'LEAGUE_STATE': 'league_state',
        'TEAMS': 'teams',
        'MATCHUPS': 'matchups',
        'PLAYERS': 'players',
        'TRANSACTIONS': 'transactions',
        'PLAYER_STATS': 'player_stats',
    }

    # Backfill dataset -> (callable, accepts_year, sync_status_item)
    BACKFILL_DATASETS = ('playoffs', 'player_stats', 'matchups', 'draft_picks', 'transactions', 'all')
    
    @staticmethod
    def record_sync_status(sync_item, success=True, error=None):
        """
        Record sync operation in SyncStatus table.
        """
        try:
            sync_status = SyncStatus(
                sync_item=sync_item,
                timestamp=datetime.utcnow(),
                success=success,
                error=error
            )
            db.session.add(sync_status)
            db.session.commit()
        except Exception as e:
            logger.error(f"Failed to record sync status for {sync_item}: {e}")
            db.session.rollback()

    
    @staticmethod
    def sync_league_state():
        """
        Synchronize league state with Sleeper API.
        """

        try:
            set_league_state()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['LEAGUE_STATE'], success=True)
            return {'success': True, 'message': 'League state synchronized'}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['LEAGUE_STATE'], success=False, error=str(e))
            return {'success': False, 'message': f'League state sync failed: {str(e)}'}


    @staticmethod
    def sync_teams():
        """
        Synchronize teams and rosters with Sleeper API.
        """
        try:
            result = synchronize_teams()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['TEAMS'], success=True)
            return {'success': True, 'message': 'Teams synchronized'}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['TEAMS'], success=False, error=str(e))
            return {'success': False, 'message': f'Teams sync failed: {str(e)}'}

    @staticmethod
    def sync_matchups():
        """
        Synchronize matchups with Sleeper API for the current week.
        """
        try:
            result = synchronize_matchups()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['MATCHUPS'], success=True)
            return {'success': True, 'message': 'Matchups synchronized', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['MATCHUPS'], success=False, error=str(e))
            return {'success': False, 'message': f'Matchups sync failed: {str(e)}'}

    @staticmethod
    def sync_players():
        """
        Synchronize players with Sleeper API.
        Updates existing players and adds new ones based on sleeper_id.
        """
        try:
            result = synchronize_players()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['PLAYERS'], success=True)
            return {'success': True, 'message': 'Players synchronized', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['PLAYERS'], success=False, error=str(e))
            return {'success': False, 'message': f'Players sync failed: {str(e)}'}

    @staticmethod
    def sync_transactions():
        """
        Synchronize transactions with Sleeper API for the current week.
        """
        try:
            result = synchronize_transactions()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['TRANSACTIONS'], success=True)
            return {'success': True, 'message': 'Transactions synchronized', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['TRANSACTIONS'], success=False, error=str(e))
            return {'success': False, 'message': f'Transactions sync failed: {str(e)}'}

    @staticmethod
    def sync_player_stats():
        """
        Synchronize per-player weekly league-scored points for the current week.
        """
        try:
            from app.logic.history import sync_current_week_player_stats
            result = sync_current_week_player_stats()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['PLAYER_STATS'], success=True)
            return {'success': True, 'message': 'Player stats synchronized', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['PLAYER_STATS'], success=False, error=str(e))
            return {'success': False, 'message': f'Player stats sync failed: {str(e)}'}

    @staticmethod
    def full_sync():
        """
        Perform a complete synchronization of Team and League State data.
        This is the main function that will be called by the scheduler.
        """
        
        sync_results = {
            'league_state': None,
            'players': None,
            'teams': None,
            'matchups': None,
            'transactions': None,
            'player_stats': None,
            'overall_success': True,
            'timestamp': datetime.utcnow()
        }
        
        try:
            league_result = SyncService.sync_league_state()
            sync_results['league_state'] = league_result
            
            if not league_result['success']:
                sync_results['overall_success'] = False
            
            players_result = SyncService.sync_players()
            sync_results['players'] = players_result
            
            if not players_result['success']:
                sync_results['overall_success'] = False
            
            # Step 3: Sync teams and rosters
            teams_result = SyncService.sync_teams()
            sync_results['teams'] = teams_result
            
            if not teams_result['success']:
                sync_results['overall_success'] = False
            
            matchups_result = SyncService.sync_matchups()
            sync_results['matchups'] = matchups_result
            
            if not matchups_result['success']:
                sync_results['overall_success'] = False

            transactions_result = SyncService.sync_transactions()
            sync_results['transactions'] = transactions_result

            if not transactions_result['success']:
                sync_results['overall_success'] = False

            player_stats_result = SyncService.sync_player_stats()
            sync_results['player_stats'] = player_stats_result

            if not player_stats_result['success']:
                sync_results['overall_success'] = False

            return sync_results
            
        except Exception as e:
            logger.error(f"Full synchronization failed with critical error: {e}")
            sync_results['overall_success'] = False
            sync_results['error'] = str(e)
            return sync_results

    # ------------------------------------------------------------------
    # Historical backfills (long-running; run in a background thread)
    # ------------------------------------------------------------------

    @staticmethod
    def backfill_status():
        """Return whether a backfill is currently running and what it is."""
        return dict(_backfill_state)

    @staticmethod
    def start_backfill(app, dataset, year=None):
        """
        Kick off a backfill in a background thread and return immediately.
        Only one backfill may run at a time.
        """
        if dataset not in SyncService.BACKFILL_DATASETS:
            return {'success': False, 'error': f'Invalid dataset. Use: {", ".join(SyncService.BACKFILL_DATASETS)}'}

        with _backfill_lock:
            if _backfill_state['running']:
                return {'success': False, 'error': f"A backfill is already running ({_backfill_state['dataset']})"}
            _backfill_state.update(running=True, dataset=dataset, started_at=datetime.utcnow().isoformat())

        thread = threading.Thread(
            target=SyncService._run_backfill_thread,
            args=(app, dataset, year),
            daemon=True,
        )
        thread.start()
        return {'success': True, 'message': f'Backfill started: {dataset}', 'dataset': dataset, 'year': year}

    @staticmethod
    def _run_backfill_thread(app, dataset, year):
        """Thread body: run the requested backfill(s) inside an app context."""
        from app.logic.history import backfill_playoffs, backfill_matchups, backfill_player_stats
        from app.logic.transactions import backfill_all_transactions
        from app.scripts.backfill_draft_picks import backfill_draft_picks

        # dataset -> (callable, accepts_year, sync_status_item)
        runners = {
            'playoffs': (backfill_playoffs, True, 'playoffs'),
            'matchups': (backfill_matchups, True, 'matchups'),
            'player_stats': (backfill_player_stats, True, 'player_stats'),
            'draft_picks': (backfill_draft_picks, False, 'draft_picks'),
            'transactions': (backfill_all_transactions, False, 'transactions'),
        }
        order = ['playoffs', 'matchups', 'player_stats', 'draft_picks', 'transactions'] if dataset == 'all' else [dataset]

        with app.app_context():
            try:
                for key in order:
                    fn, accepts_year, item = runners[key]
                    try:
                        logger.info(f'Backfill starting: {key} (year={year})')
                        fn(year) if accepts_year else fn()
                        SyncService.record_sync_status(item, success=True)
                    except Exception as e:
                        logger.error(f'Backfill {key} failed: {e}')
                        db.session.rollback()
                        SyncService.record_sync_status(item, success=False, error=str(e))
            finally:
                with _backfill_lock:
                    _backfill_state.update(running=False, dataset=None, started_at=None)
