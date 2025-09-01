import logging
from datetime import datetime
from app import db
from app.models.sync_status import SyncStatus
from app.logic.league import synchronize_teams, set_league_state, synchronize_matchups

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
    def full_sync():
        """
        Perform a complete synchronization of Team and League State data.
        This is the main function that will be called by the scheduler.
        """
        
        sync_results = {
            'league_state': None,
            'teams': None,
            'matchups': None,
            'overall_success': True,
            'timestamp': datetime.utcnow()
        }
        
        try:
            league_result = SyncService.sync_league_state()
            sync_results['league_state'] = league_result
            
            if not league_result['success']:
                sync_results['overall_success'] = False
            
            teams_result = SyncService.sync_teams()
            sync_results['teams'] = teams_result
            
            if not teams_result['success']:
                sync_results['overall_success'] = False
            
            matchups_result = SyncService.sync_matchups()
            sync_results['matchups'] = matchups_result
            
            if not matchups_result['success']:
                sync_results['overall_success'] = False
            
            return sync_results
            
        except Exception as e:
            logger.error(f"Full synchronization failed with critical error: {e}")
            sync_results['overall_success'] = False
            sync_results['error'] = str(e)
            return sync_results
