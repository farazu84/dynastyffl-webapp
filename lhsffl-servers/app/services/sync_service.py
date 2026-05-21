import logging
from datetime import datetime
from app import db
from app.models.sync_status import SyncStatus
from app.logic.league import synchronize_teams, set_league_state, synchronize_matchups, synchronize_players
from app.logic.transactions import synchronize_transactions
from app.logic.nflverse import backfill_player_ids, synchronize_nfl_draft_data, synchronize_player_game_logs

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        'NFL_DRAFT': 'nfl_draft',
        'GAME_LOGS': 'game_logs',
        'PLAYER_IDS': 'player_ids',
    }
    
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
    def sync_player_ids():
        """
        Backfill missing gsis_id and pfr_id on Players using nflverse
        players + ff_playerids datasets joined on sleeper_id.
        Should run before sync_nfl_draft() and sync_game_logs().
        """
        try:
            result = backfill_player_ids()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['PLAYER_IDS'], success=True)
            return {'success': True, 'message': 'Player IDs backfilled', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['PLAYER_IDS'], success=False, error=str(e))
            return {'success': False, 'message': f'Player ID backfill failed: {str(e)}'}

    @staticmethod
    def sync_nfl_draft():
        """
        Fetch NFL draft history from nflverse and upsert into NFLDraftData.
        Filtered to players already in the Players table (gsis_id match).
        """
        try:
            result = synchronize_nfl_draft_data()
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['NFL_DRAFT'], success=True)
            return {'success': True, 'message': 'NFL draft data synchronized', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['NFL_DRAFT'], success=False, error=str(e))
            return {'success': False, 'message': f'NFL draft sync failed: {str(e)}'}

    @staticmethod
    def sync_game_logs(season=None):
        """
        Fetch ff_opportunity data from nflverse and upsert into PlayerGameLogs.
        Filtered to players already in the Players table (gsis_id match).
        """
        try:
            result = synchronize_player_game_logs(season=season)
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['GAME_LOGS'], success=True)
            return {'success': True, 'message': 'Player game logs synchronized', 'result': result}
        except Exception as e:
            SyncService.record_sync_status(SyncService.SYNC_ITEMS['GAME_LOGS'], success=False, error=str(e))
            return {'success': False, 'message': f'Game logs sync failed: {str(e)}'}

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

            return sync_results
            
        except Exception as e:
            logger.error(f"Full synchronization failed with critical error: {e}")
            sync_results['overall_success'] = False
            sync_results['error'] = str(e)
            return sync_results
