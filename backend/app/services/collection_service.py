import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_error

from app.collectors.base_collector import BaseCollector, CollectionResult
from app.collectors.instagram_collector import InstagramCollector
from app.models.influencer import Platform, Influencer, Post, Comment, InfluencerStatus
from app.models.collection import CollectionTask, TaskStatus, TaskPriority, TaskErrorLog
from app import db
from app.config import Config

logger = logging.getLogger(__name__)

class CollectionService:
    """Service for managing influencer data collection"""
    
    def __init__(self):
        self.collectors = {}
        self._initialize_collectors()
        self.max_concurrent_tasks = 10
        self.collection_semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
    
    def _initialize_collectors(self):
        """Initialize platform-specific collectors"""
        try:
            self.collectors[Platform.INSTAGRAM] = InstagramCollector()
            # TODO: Add other collectors
            # self.collectors[Platform.YOUTUBE] = YoutubeCollector()
            # self.collectors[Platform.TIKTOK] = TiktokCollector()
            # self.collectors[Platform.TWITTER] = TwitterCollector()
            
            logger.info(f"Initialized {len(self.collectors)} collectors")
        except Exception as e:
            logger.error(f"Error initializing collectors: {e}")
    
    async def collect_influencer_profile(self, influencer_id: int, force: bool = False) -> CollectionResult:
        """Collect influencer profile data"""
        async with self.collection_semaphore:
            try:
                # Get influencer from database
                influencer = Influencer.query.get(influencer_id)
                if not influencer:
                    return CollectionResult(
                        success=False,
                        error="Influencer not found"
                    )
                
                # Check if collection is needed
                if not force and not influencer.needs_collection():
                    return CollectionResult(
                        success=True,
                        data=[],
                        items_collected=0,
                        error="Collection not needed yet"
                    )
                
                # Get appropriate collector
                collector = self.collectors.get(influencer.platform)
                if not collector:
                    return CollectionResult(
                        success=False,
                        error=f"No collector available for {influencer.platform.value}"
                    )
                
                # Create collection task
                task = CollectionTask(
                    influencer_id=influencer_id,
                    platform=influencer.platform,
                    collection_type='profile',
                    parameters={'username': influencer.username}
                )
                db.session.add(task)
                db.session.commit()
                
                # Mark task as started
                task.mark_started('collection_service')
                
                # Update influencer status
                influencer.status = InfluencerStatus.COLLECTING
                db.session.commit()
                
                # Perform collection
                result = await self._collect_with_retry(
                    collector, 
                    'collect_influencer_data',
                    influencer.username,
                    task
                )
                
                if result.success:
                    # Update influencer with collected data
                    await self._update_influencer_profile(influencer, result.data[0])
                    
                    # Mark task as completed
                    task.mark_completed(1, result.data[0])
                    
                    # Update influencer status and last collected time
                    influencer.status = InfluencerStatus.ACTIVE
                    influencer.last_collected = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"Successfully collected profile for {influencer.username}")
                else:
                    # Mark task as failed
                    task.mark_failed(result.error)
                    
                    # Update influencer status
                    influencer.status = InfluencerStatus.ERROR
                    db.session.commit()
                    
                    logger.error(f"Failed to collect profile for {influencer.username}: {result.error}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in collect_influencer_profile: {e}")
                return CollectionResult(
                    success=False,
                    error=f"Collection service error: {str(e)}"
                )
    
    async def collect_influencer_posts(self, influencer_id: int, limit: int = 50, 
                                     force: bool = False) -> CollectionResult:
        """Collect influencer posts"""
        async with self.collection_semaphore:
            try:
                influencer = Influencer.query.get(influencer_id)
                if not influencer:
                    return CollectionResult(
                        success=False,
                        error="Influencer not found"
                    )
                
                # Get collector
                collector = self.collectors.get(influencer.platform)
                if not collector:
                    return CollectionResult(
                        success=False,
                        error=f"No collector available for {influencer.platform.value}"
                    )
                
                # Create collection task
                task = CollectionTask(
                    influencer_id=influencer_id,
                    platform=influencer.platform,
                    collection_type='posts',
                    parameters={'limit': limit}
                )
                db.session.add(task)
                db.session.commit()
                
                task.mark_started('collection_service')
                
                # Perform collection
                result = await self._collect_with_retry(
                    collector,
                    'collect_posts',
                    influencer.external_id,
                    task,
                    limit=limit
                )
                
                if result.success:
                    # Save posts to database
                    saved_posts = await self._save_posts(influencer, result.data)
                    
                    task.mark_completed(len(saved_posts), {'posts_collected': len(saved_posts)})
                    
                    # Update influencer post count
                    influencer.post_count = Post.query.filter_by(influencer_id=influencer_id).count()
                    influencer.last_collected = datetime.utcnow()
                    db.session.commit()
                    
                    logger.info(f"Successfully collected {len(saved_posts)} posts for {influencer.username}")
                    
                    return CollectionResult(
                        success=True,
                        data=saved_posts,
                        items_collected=len(saved_posts)
                    )
                else:
                    task.mark_failed(result.error)
                    logger.error(f"Failed to collect posts for {influencer.username}: {result.error}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in collect_influencer_posts: {e}")
                return CollectionResult(
                    success=False,
                    error=f"Collection service error: {str(e)}"
                )
    
    async def collect_post_comments(self, post_id: int, limit: int = 100) -> CollectionResult:
        """Collect comments for a specific post"""
        async with self.collection_semaphore:
            try:
                post = Post.query.get(post_id)
                if not post:
                    return CollectionResult(
                        success=False,
                        error="Post not found"
                    )
                
                # Get collector
                collector = self.collectors.get(post.platform)
                if not collector:
                    return CollectionResult(
                        success=False,
                        error=f"No collector available for {post.platform.value}"
                    )
                
                # Create collection task
                task = CollectionTask(
                    influencer_id=post.influencer_id,
                    platform=post.platform,
                    collection_type='comments',
                    parameters={'post_id': post.external_id, 'limit': limit}
                )
                db.session.add(task)
                db.session.commit()
                
                task.mark_started('collection_service')
                
                # Perform collection
                result = await self._collect_with_retry(
                    collector,
                    'collect_comments',
                    post.external_id,
                    task,
                    limit=limit
                )
                
                if result.success:
                    # Save comments to database
                    saved_comments = await self._save_comments(post, result.data)
                    
                    task.mark_completed(len(saved_comments), {'comments_collected': len(saved_comments)})
                    
                    # Update post comment count
                    post.comments_count = Comment.query.filter_by(post_id=post_id).count()
                    db.session.commit()
                    
                    logger.info(f"Successfully collected {len(saved_comments)} comments for post {post.external_id}")
                    
                    return CollectionResult(
                        success=True,
                        data=saved_comments,
                        items_collected=len(saved_comments)
                    )
                else:
                    task.mark_failed(result.error)
                    logger.error(f"Failed to collect comments for post {post.external_id}: {result.error}")
                
                return result
                
            except Exception as e:
                logger.error(f"Error in collect_post_comments: {e}")
                return CollectionResult(
                    success=False,
                    error=f"Collection service error: {str(e)}"
                )
    
    async def _collect_with_retry(self, collector: BaseCollector, method_name: str, 
                                *args, task: CollectionTask, **kwargs) -> CollectionResult:
        """Execute collection with retry logic"""
        try:
            async with collector:
                # Authenticate collector
                if not await collector.authenticate():
                    return CollectionResult(
                        success=False,
                        error="Authentication failed"
                    )
                
                # Get the method to call
                method = getattr(collector, method_name)
                
                # Execute collection
                data = await method(*args, **kwargs)
                
                return CollectionResult(
                    success=True,
                    data=data if isinstance(data, list) else [data],
                    items_collected=len(data) if isinstance(data, list) else 1
                )
                
        except Exception as e:
            # Log error
            error_log = TaskErrorLog(
                task_id=task.id,
                error_type=type(e).__name__,
                error_message=str(e),
                retry_attempt=task.retry_count
            )
            db.session.add(error_log)
            db.session.commit()
            
            logger.error(f"Collection error in {method_name}: {e}")
            return CollectionResult(
                success=False,
                error=str(e)
            )
    
    async def _update_influencer_profile(self, influencer: Influencer, profile_data: Dict):
        """Update influencer profile with collected data"""
        try:
            influencer.display_name = profile_data.get('display_name', influencer.display_name)
            influencer.bio = profile_data.get('bio', influencer.bio)
            influencer.profile_image_url = profile_data.get('profile_image_url', influencer.profile_image_url)
            influencer.verified = profile_data.get('verified', influencer.verified)
            influencer.business_account = profile_data.get('business_account', influencer.business_account)
            influencer.follower_count = profile_data.get('follower_count', influencer.follower_count)
            influencer.following_count = profile_data.get('following_count', influencer.following_count)
            influencer.post_count = profile_data.get('post_count', influencer.post_count)
            influencer.location = profile_data.get('location', influencer.location)
            
            db.session.commit()
            logger.info(f"Updated profile for influencer {influencer.username}")
            
        except Exception as e:
            logger.error(f"Error updating influencer profile: {e}")
            db.session.rollback()
    
    async def _save_posts(self, influencer: Influencer, posts_data: List[Dict]) -> List[Dict]:
        """Save collected posts to database"""
        saved_posts = []
        
        try:
            for post_data in posts_data:
                # Check if post already exists
                existing_post = Post.query.filter_by(
                    external_id=post_data['external_id'],
                    platform=post_data['platform']
                ).first()
                
                if existing_post:
                    # Update existing post
                    existing_post.likes_count = post_data.get('likes_count', existing_post.likes_count)
                    existing_post.comments_count = post_data.get('comments_count', existing_post.comments_count)
                    existing_post.shares_count = post_data.get('shares_count', existing_post.shares_count)
                    existing_post.views_count = post_data.get('views_count', existing_post.views_count)
                    existing_post.updated_at = datetime.utcnow()
                    saved_posts.append(existing_post.to_dict())
                else:
                    # Create new post
                    new_post = Post(
                        external_id=post_data['external_id'],
                        influencer_id=influencer.id,
                        platform=post_data['platform'],
                        content=post_data.get('content', ''),
                        content_type=post_data.get('content_type', ''),
                        media_urls=post_data.get('media_urls', []),
                        hashtags=post_data.get('hashtags', []),
                        mentions=post_data.get('mentions', []),
                        likes_count=post_data.get('likes_count', 0),
                        comments_count=post_data.get('comments_count', 0),
                        shares_count=post_data.get('shares_count', 0),
                        views_count=post_data.get('views_count', 0),
                        posted_at=post_data['posted_at'],
                        language_detected=post_data.get('language_detected'),
                        location_data=post_data.get('location_data'),
                        raw_data=post_data.get('raw_data', {})
                    )
                    
                    db.session.add(new_post)
                    db.session.flush()  # Get the ID
                    saved_posts.append(new_post.to_dict())
            
            db.session.commit()
            logger.info(f"Saved {len(saved_posts)} posts for influencer {influencer.username}")
            
        except Exception as e:
            logger.error(f"Error saving posts: {e}")
            db.session.rollback()
        
        return saved_posts
    
    async def _save_comments(self, post: Post, comments_data: List[Dict]) -> List[Dict]:
        """Save collected comments to database"""
        saved_comments = []
        
        try:
            for comment_data in comments_data:
                # Check if comment already exists
                existing_comment = Comment.query.filter_by(
                    external_id=comment_data['external_id'],
                    post_id=post.id
                ).first()
                
                if existing_comment:
                    # Update existing comment
                    existing_comment.likes_count = comment_data.get('likes_count', existing_comment.likes_count)
                    existing_comment.replies_count = comment_data.get('replies_count', existing_comment.replies_count)
                    saved_comments.append(existing_comment.to_dict())
                else:
                    # Create new comment
                    new_comment = Comment(
                        external_id=comment_data['external_id'],
                        post_id=post.id,
                        content=comment_data.get('content', ''),
                        author_username=comment_data.get('author_username', ''),
                        author_display_name=comment_data.get('author_display_name', ''),
                        likes_count=comment_data.get('likes_count', 0),
                        replies_count=comment_data.get('replies_count', 0),
                        posted_at=comment_data['posted_at'],
                        language_detected=comment_data.get('language_detected')
                    )
                    
                    db.session.add(new_comment)
                    db.session.flush()  # Get the ID
                    saved_comments.append(new_comment.to_dict())
            
            db.session.commit()
            logger.info(f"Saved {len(saved_comments)} comments for post {post.external_id}")
            
        except Exception as e:
            logger.error(f"Error saving comments: {e}")
            db.session.rollback()
        
        return saved_comments
    
    async def schedule_collection_for_influencer(self, influencer_id: int, 
                                               priority: TaskPriority = TaskPriority.NORMAL) -> List[CollectionTask]:
        """Schedule collection tasks for an influencer"""
        try:
            influencer = Influencer.query.get(influencer_id)
            if not influencer:
                raise ValueError("Influencer not found")
            
            tasks = []
            
            # Schedule profile collection
            profile_task = CollectionTask(
                influencer_id=influencer_id,
                platform=influencer.platform,
                collection_type='profile',
                priority=priority,
                parameters={'username': influencer.username}
            )
            tasks.append(profile_task)
            
            # Schedule posts collection
            posts_task = CollectionTask(
                influencer_id=influencer_id,
                platform=influencer.platform,
                collection_type='posts',
                priority=priority,
                parameters={'limit': 50}
            )
            tasks.append(posts_task)
            
            # Add tasks to database
            for task in tasks:
                db.session.add(task)
            
            db.session.commit()
            
            logger.info(f"Scheduled {len(tasks)} collection tasks for influencer {influencer.username}")
            return tasks
            
        except Exception as e:
            logger.error(f"Error scheduling collection tasks: {e}")
            db.session.rollback()
            return []
    
    async def process_pending_tasks(self, max_tasks: int = 10) -> int:
        """Process pending collection tasks"""
        try:
            # Get pending tasks ordered by priority and creation time
            pending_tasks = CollectionTask.query.filter_by(
                status=TaskStatus.PENDING
            ).order_by(
                CollectionTask.priority.desc(),
                CollectionTask.created_at.asc()
            ).limit(max_tasks).all()
            
            # Also get retry tasks that are ready
            retry_tasks = CollectionTask.query.filter_by(
                status=TaskStatus.RETRY
            ).filter(
                CollectionTask.next_retry_at <= datetime.utcnow()
            ).order_by(
                CollectionTask.priority.desc(),
                CollectionTask.next_retry_at.asc()
            ).limit(max_tasks - len(pending_tasks)).all()
            
            all_tasks = pending_tasks + retry_tasks
            
            if not all_tasks:
                return 0
            
            # Process tasks concurrently
            results = await asyncio.gather(*[
                self._process_single_task(task) for task in all_tasks
            ], return_exceptions=True)
            
            successful = sum(1 for r in results if not isinstance(r, Exception))
            
            logger.info(f"Processed {len(all_tasks)} tasks, {successful} successful")
            return successful
            
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}")
            return 0
    
    async def _process_single_task(self, task: CollectionTask) -> bool:
        """Process a single collection task"""
        try:
            if task.collection_type == 'profile':
                result = await self.collect_influencer_profile(task.influencer_id)
            elif task.collection_type == 'posts':
                limit = task.parameters.get('limit', 50)
                result = await self.collect_influencer_posts(task.influencer_id, limit)
            elif task.collection_type == 'comments':
                # Find post by external_id
                post_external_id = task.parameters.get('post_id')
                post = Post.query.filter_by(external_id=post_external_id).first()
                if post:
                    limit = task.parameters.get('limit', 100)
                    result = await self.collect_post_comments(post.id, limit)
                else:
                    result = CollectionResult(success=False, error="Post not found")
            else:
                result = CollectionResult(success=False, error="Unknown collection type")
            
            return result.success
            
        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        try:
            stats = {
                'total_influencers': Influencer.query.count(),
                'active_influencers': Influencer.query.filter_by(status=InfluencerStatus.ACTIVE).count(),
                'total_posts': Post.query.count(),
                'total_comments': Comment.query.count(),
                'pending_tasks': CollectionTask.query.filter_by(status=TaskStatus.PENDING).count(),
                'running_tasks': CollectionTask.query.filter_by(status=TaskStatus.RUNNING).count(),
                'failed_tasks': CollectionTask.query.filter_by(status=TaskStatus.FAILED).count(),
                'completed_tasks_today': CollectionTask.query.filter(
                    CollectionTask.status == TaskStatus.COMPLETED,
                    CollectionTask.completed_at >= datetime.utcnow() - timedelta(days=1)
                ).count(),
                'platforms': {
                    platform.value: Influencer.query.filter_by(platform=platform).count()
                    for platform in Platform
                },
                'collectors_available': list(self.collectors.keys())
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {}