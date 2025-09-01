from flask import Blueprint, jsonify, request
from app.services.sync_service import SyncService
from app.scheduler import sync_scheduler

sync = Blueprint('sync', __name__)


@sync.route('/sync/manual', methods=['POST', 'OPTIONS'])
def trigger_manual_sync():
    """
    Trigger a manual full synchronization.
    This bypasses the scheduler and runs immediately.
    """
    try:
        # Check if a sync type is specified
        data = request.get_json() if request.is_json else {}
        sync_type = data.get('type', 'full')
        
        if sync_type == 'full':
            result = SyncService.full_sync()
        elif sync_type == 'teams':
            result = SyncService.sync_teams()
        elif sync_type == 'league_state':
            result = SyncService.sync_league_state()
        elif sync_type == 'matchups':
            result = SyncService.sync_matchups()
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid sync type. Use: full, teams, league_state, or matchups'
            }), 400
        
        return jsonify({
            'success': True,
            'message': f'Manual {sync_type} sync completed',
            'result': result
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Manual sync failed: {str(e)}'
        }), 500


@sync.route('/sync/scheduler/status', methods=['GET', 'OPTIONS'])
def get_scheduler_status():
    """
    Get detailed scheduler status and job information.
    """
    try:
        status = sync_scheduler.get_job_status()
        return jsonify({
            'success': True,
            'scheduler': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to get scheduler status: {str(e)}'
        }), 500


@sync.route('/sync/scheduler/trigger', methods=['POST', 'OPTIONS'])
def trigger_scheduled_sync():
    """
    Trigger the same sync that the scheduler would run.
    Useful for testing the scheduled sync logic manually.
    """
    try:
        result = sync_scheduler.trigger_manual_sync()
        return jsonify({
            'success': True,
            'message': 'Scheduled sync triggered manually',
            'result': result
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to trigger scheduled sync: {str(e)}'
        }), 500
