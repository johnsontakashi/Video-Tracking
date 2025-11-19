from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import logging
from datetime import datetime

from app.tasks.task_manager import task_manager
from app.models.user import User
from app.models.collection import CollectionTask, TaskStatus, TaskPriority
from app.models.influencer import Influencer
from app import db

logger = logging.getLogger(__name__)

task_bp = Blueprint('tasks', __name__, url_prefix='/api/tasks')

@task_bp.route('/health', methods=['GET'])
@jwt_required()
def task_system_health():
    """Check task system health"""
    try:
        stats = task_manager.get_queue_stats()
        return jsonify({
            'status': 'healthy' if stats.get('celery_available') else 'degraded',
            'stats': stats
        }), 200
    except Exception as e:
        logger.error(f"Task system health check failed: {e}")
        return jsonify({'error': 'Task system unavailable'}), 500

@task_bp.route('/queue/influencer/<int:influencer_id>', methods=['POST'])
@jwt_required()
def queue_influencer_collection(influencer_id):
    """Queue collection task for specific influencer"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if influencer exists and user has access
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        data = request.get_json() or {}
        priority_str = data.get('priority', 'normal').upper()
        force = data.get('force', False)
        
        try:
            priority = TaskPriority[priority_str]
        except KeyError:
            return jsonify({'error': 'Invalid priority level'}), 400
        
        # Queue the task
        task_id = task_manager.queue_influencer_collection(
            influencer_id, priority, force
        )
        
        if task_id:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': f'Collection task queued for {influencer.username}'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue collection task'
            }), 500
            
    except Exception as e:
        logger.error(f"Error queueing influencer collection: {e}")
        return jsonify({'error': 'Failed to queue collection task'}), 500

@task_bp.route('/queue/analytics/<int:influencer_id>', methods=['POST'])
@jwt_required()
def queue_analytics_processing(influencer_id):
    """Queue analytics processing for influencer"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        
        # Queue analytics task
        task_id = task_manager.queue_analytics_processing(influencer_id, days_back)
        
        if task_id:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': f'Analytics processing queued for {influencer.username}'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue analytics task'
            }), 500
            
    except Exception as e:
        logger.error(f"Error queueing analytics processing: {e}")
        return jsonify({'error': 'Failed to queue analytics task'}), 500

@task_bp.route('/queue/comments/<int:post_id>', methods=['POST'])
@jwt_required()
def queue_comment_collection(post_id):
    """Queue comment collection for a post"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json() or {}
        limit = min(data.get('limit', 100), 1000)  # Cap at 1000 comments
        
        # Queue comment collection task
        task_id = task_manager.queue_comment_collection(post_id, limit)
        
        if task_id:
            return jsonify({
                'success': True,
                'task_id': task_id,
                'message': f'Comment collection queued for post {post_id}'
            }), 201
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to queue comment collection task'
            }), 500
            
    except Exception as e:
        logger.error(f"Error queueing comment collection: {e}")
        return jsonify({'error': 'Failed to queue comment collection task'}), 500

@task_bp.route('/status/<task_id>', methods=['GET'])
@jwt_required()
def get_task_status(task_id):
    """Get detailed status of a specific task"""
    try:
        status = task_manager.get_task_status(task_id)
        return jsonify(status), 200
        
    except Exception as e:
        logger.error(f"Error getting task status: {e}")
        return jsonify({'error': 'Failed to get task status'}), 500

@task_bp.route('/cancel/<task_id>', methods=['POST'])
@jwt_required()
def cancel_task(task_id):
    """Cancel a running or pending task"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if user has permission to cancel task
        # (For now, users can cancel their own tasks or admins can cancel any)
        task = CollectionTask.query.filter_by(task_id=task_id).first()
        if task and not user.is_admin():
            # Add additional permission checks if needed
            pass
        
        success = task_manager.cancel_task(task_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Task cancelled successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to cancel task'
            }), 400
            
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        return jsonify({'error': 'Failed to cancel task'}), 500

@task_bp.route('/retry/<task_id>', methods=['POST'])
@jwt_required()
def retry_task(task_id):
    """Retry a failed task"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        new_task_id = task_manager.retry_failed_task(task_id)
        
        if new_task_id:
            return jsonify({
                'success': True,
                'new_task_id': new_task_id,
                'message': 'Task retry initiated'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to retry task or task cannot be retried'
            }), 400
            
    except Exception as e:
        logger.error(f"Error retrying task: {e}")
        return jsonify({'error': 'Failed to retry task'}), 500

@task_bp.route('/list', methods=['GET'])
@jwt_required()
def list_tasks():
    """List tasks with filtering and pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        influencer_id = request.args.get('influencer_id', type=int)
        collection_type = request.args.get('collection_type')
        
        query = CollectionTask.query
        
        # Apply filters
        if status_filter:
            try:
                status_enum = TaskStatus(status_filter.lower())
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': 'Invalid status filter'}), 400
        
        if influencer_id:
            query = query.filter_by(influencer_id=influencer_id)
        
        if collection_type:
            query = query.filter_by(collection_type=collection_type)
        
        # Order by creation time (newest first)
        query = query.order_by(CollectionTask.created_at.desc())
        
        # Paginate
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Convert to dict and add Celery status if available
        tasks = []
        for task in paginated.items:
            task_dict = task.to_dict()
            
            # Add real-time Celery status
            if task.task_id:
                celery_status = task_manager.get_task_status(str(task.task_id))
                task_dict['celery_status'] = celery_status.get('celery_status')
            
            tasks.append(task_dict)
        
        return jsonify({
            'tasks': tasks,
            'pagination': {
                'page': page,
                'pages': paginated.pages,
                'per_page': per_page,
                'total': paginated.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        return jsonify({'error': 'Failed to retrieve tasks'}), 500

@task_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_task_stats():
    """Get comprehensive task statistics"""
    try:
        stats = task_manager.get_queue_stats()
        
        # Add database statistics
        task_counts = {}
        for status in TaskStatus:
            count = CollectionTask.query.filter_by(status=status).count()
            task_counts[status.value] = count
        
        stats['db_task_counts'] = task_counts
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting task stats: {e}")
        return jsonify({'error': 'Failed to retrieve task statistics'}), 500

@task_bp.route('/schedule', methods=['GET'])
@jwt_required()
def get_collection_schedule():
    """Get recommended collection schedule"""
    try:
        schedule = task_manager.get_influencer_collection_schedule()
        return jsonify({
            'schedule': schedule,
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting collection schedule: {e}")
        return jsonify({'error': 'Failed to retrieve collection schedule'}), 500

@task_bp.route('/bulk/queue', methods=['POST'])
@jwt_required()
def bulk_queue_tasks():
    """Queue tasks for multiple influencers"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        influencer_ids = data.get('influencer_ids', [])
        priority_str = data.get('priority', 'normal').upper()
        force = data.get('force', False)
        
        if not influencer_ids:
            return jsonify({'error': 'No influencer IDs provided'}), 400
        
        if len(influencer_ids) > 50:  # Limit bulk operations
            return jsonify({'error': 'Too many influencers (max 50)'}), 400
        
        try:
            priority = TaskPriority[priority_str]
        except KeyError:
            return jsonify({'error': 'Invalid priority level'}), 400
        
        results = []
        
        for influencer_id in influencer_ids:
            try:
                task_id = task_manager.queue_influencer_collection(
                    influencer_id, priority, force
                )
                
                results.append({
                    'influencer_id': influencer_id,
                    'success': bool(task_id),
                    'task_id': task_id
                })
                
            except Exception as e:
                results.append({
                    'influencer_id': influencer_id,
                    'success': False,
                    'error': str(e)
                })
        
        successful = sum(1 for r in results if r['success'])
        
        return jsonify({
            'success': successful > 0,
            'total_queued': successful,
            'total_requested': len(influencer_ids),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk queue operation: {e}")
        return jsonify({'error': 'Bulk queue operation failed'}), 500

# Admin routes
@task_bp.route('/admin/purge', methods=['POST'])
@jwt_required()
def admin_purge_completed():
    """Admin: Purge old completed tasks"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        data = request.get_json() or {}
        older_than_days = data.get('older_than_days', 7)
        
        deleted_count = task_manager.purge_completed_tasks(older_than_days)
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'Purged {deleted_count} completed tasks'
        }), 200
        
    except Exception as e:
        logger.error(f"Error purging tasks: {e}")
        return jsonify({'error': 'Failed to purge completed tasks'}), 500

@task_bp.route('/admin/scaling', methods=['GET'])
@jwt_required()
def admin_scaling_recommendations():
    """Admin: Get worker scaling recommendations"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        recommendations = task_manager.auto_scale_workers()
        
        return jsonify(recommendations), 200
        
    except Exception as e:
        logger.error(f"Error getting scaling recommendations: {e}")
        return jsonify({'error': 'Failed to get scaling recommendations'}), 500

@task_bp.route('/admin/force-schedule', methods=['POST'])
@jwt_required()
def admin_force_schedule():
    """Admin: Force schedule collection for all due influencers"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Trigger the schedule_collections task manually
        from app.tasks.collection_tasks import schedule_collections
        
        result = schedule_collections.delay()
        
        return jsonify({
            'success': True,
            'task_id': result.id,
            'message': 'Forced collection scheduling initiated'
        }), 200
        
    except Exception as e:
        logger.error(f"Error forcing schedule: {e}")
        return jsonify({'error': 'Failed to force collection scheduling'}), 500