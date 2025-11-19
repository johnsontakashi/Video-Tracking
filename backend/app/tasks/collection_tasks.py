import asyncio
import logging
from datetime import datetime, timedelta
from celery import Celery
from celery.schedules import crontab
from sqlalchemy.orm import sessionmaker

from app import create_app, db
from app.services.collection_service import CollectionService
from app.services.analytics_service import AnalyticsService
from app.models.influencer import Influencer, InfluencerStatus
from app.models.collection import CollectionTask, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)

# Create Flask app and Celery instance
app = create_app()
celery = app.extensions['celery']

@celery.task(bind=True, name='tasks.collect_influencer_data')
def collect_influencer_data(self, influencer_id: int, force: bool = False):
    """
    Celery task to collect data for a specific influencer
    """
    with app.app_context():
        try:
            logger.info(f"Starting collection for influencer {influencer_id}")
            
            # Initialize collection service
            collection_service = CollectionService()
            
            # Run async collection in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    collection_service.collect_influencer_profile(influencer_id, force=force)
                )
                
                if result.success:
                    # Also collect posts if profile collection succeeded
                    posts_result = loop.run_until_complete(
                        collection_service.collect_influencer_posts(influencer_id, limit=50, force=force)
                    )
                    
                    logger.info(f"Collection completed for influencer {influencer_id}: "
                              f"Profile: {result.success}, Posts: {posts_result.success}")
                    
                    return {
                        'success': True,
                        'influencer_id': influencer_id,
                        'profile_collected': result.items_collected,
                        'posts_collected': posts_result.items_collected if posts_result.success else 0,
                        'completed_at': datetime.utcnow().isoformat()
                    }
                else:
                    logger.error(f"Collection failed for influencer {influencer_id}: {result.error}")
                    return {
                        'success': False,
                        'influencer_id': influencer_id,
                        'error': result.error,
                        'completed_at': datetime.utcnow().isoformat()
                    }
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Task error collecting influencer {influencer_id}: {e}")
            
            # Mark task as failed and schedule retry if needed
            self.retry(countdown=60 * (2 ** self.request.retries), max_retries=3)
            
            return {
                'success': False,
                'influencer_id': influencer_id,
                'error': str(e),
                'retry_count': self.request.retries,
                'completed_at': datetime.utcnow().isoformat()
            }

@celery.task(bind=True, name='tasks.collect_post_comments')
def collect_post_comments(self, post_id: int, limit: int = 100):
    """
    Celery task to collect comments for a specific post
    """
    with app.app_context():
        try:
            logger.info(f"Starting comment collection for post {post_id}")
            
            collection_service = CollectionService()
            
            # Run async collection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    collection_service.collect_post_comments(post_id, limit=limit)
                )
                
                logger.info(f"Comment collection completed for post {post_id}: "
                          f"Success: {result.success}, Comments: {result.items_collected}")
                
                return {
                    'success': result.success,
                    'post_id': post_id,
                    'comments_collected': result.items_collected,
                    'error': result.error if not result.success else None,
                    'completed_at': datetime.utcnow().isoformat()
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Task error collecting comments for post {post_id}: {e}")
            
            self.retry(countdown=60 * (2 ** self.request.retries), max_retries=3)
            
            return {
                'success': False,
                'post_id': post_id,
                'error': str(e),
                'retry_count': self.request.retries,
                'completed_at': datetime.utcnow().isoformat()
            }

@celery.task(name='tasks.process_analytics')
def process_analytics(influencer_id: int, days_back: int = 30):
    """
    Celery task to process analytics for an influencer
    """
    with app.app_context():
        try:
            logger.info(f"Starting analytics processing for influencer {influencer_id}")
            
            # Get influencer
            influencer = Influencer.query.get(influencer_id)
            if not influencer:
                return {
                    'success': False,
                    'error': f"Influencer {influencer_id} not found"
                }
            
            analytics_service = AnalyticsService()
            
            # Run async analytics processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # Calculate comprehensive analytics
                analytics = loop.run_until_complete(
                    analytics_service.calculate_influencer_analytics(influencer, days_back)
                )
                
                if analytics:
                    logger.info(f"Analytics completed for influencer {influencer_id}: "
                              f"Influence Score: {analytics.influence_score:.2f}")
                    
                    return {
                        'success': True,
                        'influencer_id': influencer_id,
                        'influence_score': analytics.influence_score,
                        'engagement_rate': analytics.engagement_rate,
                        'posts_analyzed': analytics.posts_analyzed,
                        'completed_at': datetime.utcnow().isoformat()
                    }
                else:
                    return {
                        'success': False,
                        'influencer_id': influencer_id,
                        'error': "Analytics calculation failed"
                    }
                    
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Analytics processing error for influencer {influencer_id}: {e}")
            return {
                'success': False,
                'influencer_id': influencer_id,
                'error': str(e)
            }

@celery.task(name='tasks.bulk_sentiment_analysis')
def bulk_sentiment_analysis(batch_size: int = 100):
    """
    Celery task for bulk sentiment analysis processing
    """
    with app.app_context():
        try:
            logger.info(f"Starting bulk sentiment analysis (batch size: {batch_size})")
            
            analytics_service = AnalyticsService()
            
            # Run async sentiment processing
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                processed_count = loop.run_until_complete(
                    analytics_service.process_bulk_sentiment_analysis(batch_size)
                )
                
                logger.info(f"Bulk sentiment analysis completed: {processed_count} posts processed")
                
                return {
                    'success': True,
                    'processed_count': processed_count,
                    'completed_at': datetime.utcnow().isoformat()
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Bulk sentiment analysis error: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0
            }

@celery.task(name='tasks.detect_trending_topics')
def detect_trending_topics(hours_back: int = 24):
    """
    Celery task to detect trending topics
    """
    with app.app_context():
        try:
            logger.info(f"Starting trending topics detection (last {hours_back} hours)")
            
            analytics_service = AnalyticsService()
            
            # Run async trending detection
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                trending_topics = loop.run_until_complete(
                    analytics_service.detect_trending_topics(hours_back)
                )
                
                logger.info(f"Trending detection completed: {len(trending_topics)} topics found")
                
                return {
                    'success': True,
                    'topics_found': len(trending_topics),
                    'topics': [topic.topic for topic in trending_topics],
                    'completed_at': datetime.utcnow().isoformat()
                }
                
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Trending topics detection error: {e}")
            return {
                'success': False,
                'error': str(e),
                'topics_found': 0
            }

@celery.task(name='tasks.schedule_collections')
def schedule_collections():
    """
    Periodic task to schedule collection for influencers that need updates
    """
    with app.app_context():
        try:
            logger.info("Starting scheduled collection check")
            
            # Find influencers that need collection
            influencers_needing_collection = Influencer.query.filter(
                Influencer.status == InfluencerStatus.ACTIVE
            ).filter(
                db.or_(
                    Influencer.last_collected.is_(None),
                    Influencer.last_collected < datetime.utcnow() - timedelta(hours=24)
                )
            ).order_by(Influencer.priority_score.desc()).limit(50).all()
            
            scheduled_count = 0
            
            for influencer in influencers_needing_collection:
                # Check if there's already a pending/running task for this influencer
                existing_task = CollectionTask.query.filter(
                    CollectionTask.influencer_id == influencer.id,
                    CollectionTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
                ).first()
                
                if not existing_task:
                    # Schedule collection task
                    collect_influencer_data.delay(influencer.id, force=False)
                    scheduled_count += 1
            
            logger.info(f"Scheduled collection for {scheduled_count} influencers")
            
            return {
                'success': True,
                'scheduled_count': scheduled_count,
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Schedule collections error: {e}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_count': 0
            }

@celery.task(name='tasks.cleanup_old_data')
def cleanup_old_data(retention_days: int = 90):
    """
    Periodic task to cleanup old data based on retention policies
    """
    with app.app_context():
        try:
            logger.info(f"Starting data cleanup (retention: {retention_days} days)")
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Clean up old collection tasks
            old_tasks = CollectionTask.query.filter(
                CollectionTask.completed_at < cutoff_date,
                CollectionTask.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED])
            ).count()
            
            CollectionTask.query.filter(
                CollectionTask.completed_at < cutoff_date,
                CollectionTask.status.in_([TaskStatus.COMPLETED, TaskStatus.FAILED])
            ).delete()
            
            # Clean up old analytics data for free tier users
            # This would be based on user subscription plans
            
            db.session.commit()
            
            logger.info(f"Data cleanup completed: {old_tasks} tasks removed")
            
            return {
                'success': True,
                'tasks_removed': old_tasks,
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Data cleanup error: {e}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e),
                'tasks_removed': 0
            }

@celery.task(name='tasks.update_influence_scores')
def update_influence_scores():
    """
    Periodic task to update influence scores for all active influencers
    """
    with app.app_context():
        try:
            logger.info("Starting influence score updates")
            
            # Get influencers that haven't had analytics updated recently
            influencers = Influencer.query.filter(
                Influencer.status == InfluencerStatus.ACTIVE
            ).filter(
                db.or_(
                    ~Influencer.analytics.any(),  # No analytics yet
                    db.exists().where(
                        # Has analytics older than 7 days
                        db.and_(
                            InfluencerAnalytics.influencer_id == Influencer.id,
                            InfluencerAnalytics.computed_at < datetime.utcnow() - timedelta(days=7)
                        )
                    )
                )
            ).order_by(Influencer.follower_count.desc()).limit(20).all()
            
            updated_count = 0
            
            for influencer in influencers:
                # Schedule analytics processing
                process_analytics.delay(influencer.id, days_back=30)
                updated_count += 1
            
            logger.info(f"Scheduled influence score updates for {updated_count} influencers")
            
            return {
                'success': True,
                'scheduled_updates': updated_count,
                'completed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Influence score update error: {e}")
            return {
                'success': False,
                'error': str(e),
                'scheduled_updates': 0
            }

# Periodic task scheduling
@celery.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Configure periodic tasks"""
    
    # Schedule collections every 4 hours
    sender.add_periodic_task(
        crontab(minute=0, hour='*/4'),
        schedule_collections.s(),
        name='schedule_collections_every_4h'
    )
    
    # Bulk sentiment analysis every 2 hours
    sender.add_periodic_task(
        crontab(minute=30, hour='*/2'),
        bulk_sentiment_analysis.s(batch_size=200),
        name='bulk_sentiment_analysis_every_2h'
    )
    
    # Detect trending topics every hour
    sender.add_periodic_task(
        crontab(minute=15),
        detect_trending_topics.s(hours_back=24),
        name='detect_trending_hourly'
    )
    
    # Update influence scores daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        update_influence_scores.s(),
        name='update_influence_scores_daily'
    )
    
    # Cleanup old data weekly on Sunday at 3 AM
    sender.add_periodic_task(
        crontab(hour=3, minute=0, day_of_week=0),
        cleanup_old_data.s(retention_days=90),
        name='cleanup_old_data_weekly'
    )
    
    logger.info("Periodic tasks configured successfully")