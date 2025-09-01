import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from app.services.sync_service import SyncService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncScheduler:
    """
    Manages the automated scheduling of Sleeper API synchronization tasks.
    Uses APScheduler to run daily sync operations in the background.
    """

    def __init__(self):
        self.scheduler = None
        self.is_running = False
        self.app = None
        
        # Default sync time is 2AM PST. After league waivers have been processed.
        self.sync_hour = int(os.getenv('SYNC_HOUR', '9'))
        self.sync_minute = int(os.getenv('SYNC_MINUTE', '0'))
        self.timezone = os.getenv('SYNC_TIMEZONE', 'UTC')

        self.enabled = os.getenv('ENABLE_SCHEDULER', 'false').lower() == 'true'
        
        logger.info(f"Scheduler configured: enabled={self.enabled}, time={self.sync_hour:02d}:{self.sync_minute:02d} {self.timezone}")
    
    def create_scheduler(self):
        """
        Create and configure the APScheduler instance.
        """

        if self.scheduler is not None:
            return self.scheduler
            
        # Configure executor for background tasks
        executors = {
            'default': ThreadPoolExecutor(max_workers=2)
        }
        
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 3600
        }
        
        self.scheduler = BackgroundScheduler(
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.timezone
        )
        
        return self.scheduler
    
    def schedule_daily_sync(self):
        """
        Schedule the daily full sync job.
        """

        if not self.enabled:
            return
            
        scheduler = self.create_scheduler()
        
        trigger = CronTrigger(
            hour=self.sync_hour,
            minute=self.sync_minute,
            timezone=self.timezone
        )
        
        scheduler.add_job(
            func=self._execute_daily_sync,
            trigger=trigger,
            id='daily_sleeper_sync',
            name='Daily Sleeper API Synchronization',
            replace_existing=True
        )
        
        logger.info(f"Daily sync job scheduled for {self.sync_hour:02d}:{self.sync_minute:02d} {self.timezone}")
    
    def _execute_daily_sync(self):
        """
        Execute the daily sync operation.
        This is the function that gets called by the scheduler.
        """
        
        if not self.app:
            logger.error("No Flask app context available for sync")
            return
        
        try:
            # Execute sync within Flask application context
            with self.app.app_context():
                SyncService.full_sync()
                
        except Exception as e:
            logger.error(f"=== Daily sync failed with critical error: {e} ===")
    
    def start(self):
        """
        Start the scheduler.
        """

        if not self.enabled:
            logger.info("Scheduler start requested but scheduler is disabled")
            return False
            
        if self.is_running:
            logger.warning("Scheduler is already running")
            return True
            
        try:
            scheduler = self.create_scheduler()
            self.schedule_daily_sync()
            scheduler.start()
            self.is_running = True
            logger.info("Scheduler started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            return False
    
    def stop(self):
        """
        Stop the scheduler.
        """

        if not self.is_running or self.scheduler is None:
            return
            
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
    
    def get_job_status(self):
        """
        Get the status of scheduled jobs.
        """

        if not self.is_running or self.scheduler is None:
            return {'status': 'stopped', 'jobs': []}
            
        try:
            jobs = []
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return {
                'status': 'running',
                'jobs': jobs,
                'scheduler_enabled': self.enabled
            }
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def trigger_manual_sync(self):
        """
        Trigger a manual sync outside of the scheduled time.
        """
        
        if not self.app:
            return {'success': False, 'error': 'No app context available'}
        
        try:
            with self.app.app_context():
                SyncService.full_sync()
                return {'success': True, 'message': 'Manual sync completed'}
        except Exception as e:
            logger.error(f"Manual sync failed: {e}")
            return {'success': False, 'error': str(e)}


sync_scheduler = SyncScheduler()
