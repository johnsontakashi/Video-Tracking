import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from celery import Celery
from celery.result import AsyncResult
from sqlalchemy import text

from app import create_app, db
from app.models.collection import CollectionTask, TaskStatus, TaskPriority
from app.models.influencer import Influencer, InfluencerStatus

logger = logging.getLogger(__name__)

class TaskManager:
    """Advanced task management for Celery jobs"""
    
    def __init__(self):
        self.app = create_app()
        self.celery = self.app.extensions.get('celery')
        
    def queue_influencer_collection(self, influencer_id: int, priority: TaskPriority = TaskPriority.NORMAL,
                                  force: bool = False) -> Optional[str]:
        """Queue collection task for an influencer"""
        try:
            with self.app.app_context():
                # Check if influencer exists and is active
                influencer = Influencer.query.get(influencer_id)
                if not influencer:
                    logger.error(f"Influencer {influencer_id} not found")
                    return None
                
                # Check for existing pending/running tasks
                existing_task = CollectionTask.query.filter(
                    CollectionTask.influencer_id == influencer_id,
                    CollectionTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
                ).first()
                
                if existing_task and not force:
                    logger.info(f"Task already exists for influencer {influencer_id}: {existing_task.id}")
                    return str(existing_task.task_id)
                
                # Create collection task record
                task = CollectionTask(
                    influencer_id=influencer_id,
                    platform=influencer.platform,
                    collection_type='profile_and_posts',
                    priority=priority,
                    parameters={'force': force}
                )
                
                db.session.add(task)
                db.session.flush()  # Get the ID
                
                # Queue the Celery task
                from app.tasks.collection_tasks import collect_influencer_data
                celery_result = collect_influencer_data.apply_async(
                    args=[influencer_id, force],
                    priority=priority.value,
                    task_id=str(task.task_id)
                )
                
                # Update task status
                task.status = TaskStatus.PENDING
                db.session.commit()
                
                logger.info(f"Queued collection task for influencer {influencer_id}: {task.task_id}")
                return str(task.task_id)
                
        except Exception as e:
            logger.error(f"Error queueing collection task: {e}")
            db.session.rollback()
            return None
    
    def queue_analytics_processing(self, influencer_id: int, days_back: int = 30) -> Optional[str]:
        """Queue analytics processing task"""
        try:
            with self.app.app_context():
                from app.tasks.collection_tasks import process_analytics
                
                celery_result = process_analytics.apply_async(
                    args=[influencer_id, days_back],
                    priority=5  # Normal priority
                )
                
                logger.info(f"Queued analytics task for influencer {influencer_id}: {celery_result.id}")
                return celery_result.id
                
        except Exception as e:
            logger.error(f"Error queueing analytics task: {e}")
            return None
    
    def queue_comment_collection(self, post_id: int, limit: int = 100) -> Optional[str]:
        """Queue comment collection task for a post"""
        try:
            with self.app.app_context():
                from app.tasks.collection_tasks import collect_post_comments
                
                celery_result = collect_post_comments.apply_async(
                    args=[post_id, limit],
                    priority=3  # Lower priority for comments
                )
                
                logger.info(f"Queued comment collection for post {post_id}: {celery_result.id}")
                return celery_result.id
                
        except Exception as e:
            logger.error(f"Error queueing comment collection: {e}")
            return None
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get detailed status of a task"""
        try:
            with self.app.app_context():
                # Check database record first
                task = CollectionTask.query.filter_by(task_id=task_id).first()
                
                if task:
                    result = {
                        'id': task_id,
                        'db_status': task.status.value,
                        'collection_type': task.collection_type,
                        'influencer_id': task.influencer_id,
                        'created_at': task.created_at.isoformat(),
                        'started_at': task.started_at.isoformat() if task.started_at else None,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                        'items_collected': task.items_collected,
                        'error_message': task.error_message,
                        'retry_count': task.retry_count
                    }
                else:
                    result = {'id': task_id, 'db_status': 'not_found'}
                
                # Get Celery task status
                if self.celery:
                    celery_result = AsyncResult(task_id, app=self.celery)
                    result.update({
                        'celery_status': celery_result.status,
                        'celery_result': celery_result.result if celery_result.ready() else None,
                        'celery_traceback': celery_result.traceback if celery_result.failed() else None
                    })
                
                return result
                
        except Exception as e:
            logger.error(f"Error getting task status: {e}")
            return {'id': task_id, 'error': str(e)}
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or pending task"""
        try:
            with self.app.app_context():
                # Cancel in Celery
                if self.celery:
                    self.celery.control.revoke(task_id, terminate=True)
                
                # Update database record
                task = CollectionTask.query.filter_by(task_id=task_id).first()
                if task and task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                    task.status = TaskStatus.CANCELLED
                    db.session.commit()
                
                logger.info(f"Cancelled task {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error cancelling task: {e}")
            return False
    
    def retry_failed_task(self, task_id: str) -> Optional[str]:
        """Retry a failed task"""
        try:
            with self.app.app_context():
                task = CollectionTask.query.filter_by(task_id=task_id).first()
                
                if not task or task.status != TaskStatus.FAILED:
                    logger.error(f"Task {task_id} not found or not in failed state")
                    return None
                
                if task.retry_count >= task.max_retries:
                    logger.error(f"Task {task_id} has exceeded max retries")
                    return None
                
                # Create new task based on the failed one
                if task.collection_type == 'profile_and_posts':
                    new_task_id = self.queue_influencer_collection(
                        task.influencer_id,
                        task.priority,
                        force=task.parameters.get('force', False)
                    )
                else:
                    logger.error(f"Unknown collection type: {task.collection_type}")
                    return None
                
                # Update original task
                task.retry_count += 1
                db.session.commit()
                
                logger.info(f"Retried task {task_id} as {new_task_id}")
                return new_task_id
                
        except Exception as e:
            logger.error(f"Error retrying task: {e}")
            return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics and health"""
        try:
            stats = {
                'celery_available': self.celery is not None,
                'queues': {},
                'workers': {},
                'task_counts': {}
            }
            
            if self.celery:
                # Get queue information
                inspect = self.celery.control.inspect()
                
                # Active tasks
                active_tasks = inspect.active()
                if active_tasks:
                    stats['active_tasks'] = sum(len(tasks) for tasks in active_tasks.values())
                    stats['workers'] = list(active_tasks.keys())
                else:
                    stats['active_tasks'] = 0
                    stats['workers'] = []
                
                # Scheduled tasks
                scheduled_tasks = inspect.scheduled()
                if scheduled_tasks:
                    stats['scheduled_tasks'] = sum(len(tasks) for tasks in scheduled_tasks.values())
                else:
                    stats['scheduled_tasks'] = 0
            
            # Database task statistics
            with self.app.app_context():
                for status in TaskStatus:
                    count = CollectionTask.query.filter_by(status=status).count()
                    stats['task_counts'][status.value] = count
                
                # Recent activity
                recent_tasks = CollectionTask.query.filter(
                    CollectionTask.created_at >= datetime.utcnow() - timedelta(hours=24)
                ).count()
                stats['tasks_last_24h'] = recent_tasks
                
                # Failed tasks in last hour (for alerting)
                failed_recent = CollectionTask.query.filter(
                    CollectionTask.status == TaskStatus.FAILED,
                    CollectionTask.updated_at >= datetime.utcnow() - timedelta(hours=1)
                ).count()
                stats['failed_last_hour'] = failed_recent
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting queue stats: {e}")
            return {'error': str(e)}
    
    def purge_completed_tasks(self, older_than_days: int = 7) -> int:
        """Remove completed task records older than specified days"""
        try:
            with self.app.app_context():
                cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)
                
                deleted_count = CollectionTask.query.filter(
                    CollectionTask.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED]),
                    CollectionTask.completed_at < cutoff_date
                ).delete()
                
                db.session.commit()
                
                logger.info(f"Purged {deleted_count} completed tasks older than {older_than_days} days")
                return deleted_count
                
        except Exception as e:
            logger.error(f"Error purging completed tasks: {e}")
            db.session.rollback()
            return 0
    
    def get_influencer_collection_schedule(self) -> List[Dict[str, Any]]:
        """Get recommended collection schedule for influencers"""
        try:
            with self.app.app_context():
                # Find influencers that need collection
                query = text("""
                    SELECT 
                        i.id,
                        i.username,
                        i.platform,
                        i.priority_score,
                        i.last_collected,
                        i.collection_frequency,
                        EXTRACT(EPOCH FROM (NOW() - COALESCE(i.last_collected, '1970-01-01'::timestamp))) / 3600 as hours_since_collection,
                        CASE 
                            WHEN ct.id IS NOT NULL THEN 'has_pending_task'
                            WHEN COALESCE(i.last_collected, '1970-01-01'::timestamp) < NOW() - INTERVAL '1 hour' * i.collection_frequency THEN 'needs_collection'
                            ELSE 'up_to_date'
                        END as collection_status
                    FROM influencers i
                    LEFT JOIN collection_tasks ct ON i.id = ct.influencer_id 
                        AND ct.status IN ('pending', 'running')
                    WHERE i.status = 'active'
                    ORDER BY 
                        i.priority_score DESC,
                        hours_since_collection DESC
                """)
                
                result = db.session.execute(query)
                
                schedule = []
                for row in result:
                    schedule.append({
                        'influencer_id': row.id,
                        'username': row.username,
                        'platform': row.platform,
                        'priority_score': float(row.priority_score),
                        'last_collected': row.last_collected.isoformat() if row.last_collected else None,
                        'hours_since_collection': float(row.hours_since_collection),
                        'collection_frequency': row.collection_frequency,
                        'status': row.collection_status
                    })
                
                return schedule
                
        except Exception as e:
            logger.error(f"Error getting collection schedule: {e}")
            return []
    
    def auto_scale_workers(self) -> Dict[str, Any]:
        """Auto-scale Celery workers based on queue load"""
        try:
            stats = self.get_queue_stats()
            
            pending_tasks = stats['task_counts'].get('pending', 0)
            running_tasks = stats.get('active_tasks', 0)
            available_workers = len(stats.get('workers', []))
            
            recommendations = {
                'current_workers': available_workers,
                'active_tasks': running_tasks,
                'pending_tasks': pending_tasks,
                'recommendation': 'maintain'
            }
            
            # Simple scaling logic
            total_load = pending_tasks + running_tasks
            
            if total_load > available_workers * 10:  # High load
                recommendations['recommendation'] = 'scale_up'
                recommendations['suggested_workers'] = min(available_workers + 2, 10)
            elif total_load < available_workers * 2 and available_workers > 2:  # Low load
                recommendations['recommendation'] = 'scale_down'
                recommendations['suggested_workers'] = max(available_workers - 1, 2)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error in auto-scale calculation: {e}")
            return {'error': str(e)}

# Global task manager instance
task_manager = TaskManager()