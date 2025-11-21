#!/usr/bin/env python3
"""
Celery application entry point for distributed task processing
"""

import os
from celery import Celery
from app import create_app

def create_celery_app():
    """Create and configure Celery app"""
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    
    # Update Celery configuration
    celery.conf.update(
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
        
        # Task routing
        task_routes={
            'tasks.collect_*': {'queue': 'collection'},
            'tasks.process_analytics': {'queue': 'analytics'},
            'tasks.bulk_sentiment_analysis': {'queue': 'analytics'},
            'tasks.detect_trending_topics': {'queue': 'analytics'},
            'tasks.schedule_collections': {'queue': 'scheduler'},
            'tasks.cleanup_old_data': {'queue': 'maintenance'},
            'tasks.update_influence_scores': {'queue': 'analytics'},
        },
        
        # Task execution settings
        task_always_eager=False,  # Set to True for synchronous execution in testing
        task_eager_propagates=True,
        task_ignore_result=False,
        task_store_eager_result=True,
        
        # Worker settings
        worker_prefetch_multiplier=1,  # Disable prefetching for fair distribution
        worker_max_tasks_per_child=1000,  # Restart workers after 1000 tasks
        worker_disable_rate_limits=False,
        
        # Task retry settings
        task_acks_late=True,  # Acknowledge task after completion
        task_reject_on_worker_lost=True,
        
        # Result backend settings
        result_expires=3600,  # Results expire after 1 hour
        result_cache_max=10000,
        
        # Beat (scheduler) settings
        beat_schedule_filename='celerybeat-schedule',
        
        # Security
        worker_hijack_root_logger=False,
        worker_log_color=False,
        
        # Monitoring
        task_send_sent_event=True,
        worker_send_task_events=True,
        
        # Error handling
        task_soft_time_limit=300,  # 5 minutes soft limit
        task_time_limit=600,       # 10 minutes hard limit
        
        # Queue priorities
        task_default_priority=5,
        worker_direct=True,
        
        # Concurrency
        worker_concurrency=4,  # Can be overridden by command line
    )
    
    # Task context configuration
    class ContextTask(celery.Task):
        """Make celery tasks work with Flask app context"""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    
    celery.Task = ContextTask
    
    # Store app reference
    app.extensions['celery'] = celery
    
    return celery

# Create the Celery app
celery_app = create_celery_app()

# Import tasks to register them
from app.tasks import collection_tasks

if __name__ == '__main__':
    celery_app.start()