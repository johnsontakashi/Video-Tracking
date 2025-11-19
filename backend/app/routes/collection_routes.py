from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import logging

from app.services.collection_service import CollectionService
from app.models.influencer import Influencer, Platform
from app.models.collection import CollectionTask, TaskStatus, TaskPriority
from app import db

logger = logging.getLogger(__name__)

collection_bp = Blueprint('collection', __name__, url_prefix='/api/collection')

# Initialize collection service
collection_service = CollectionService()

@collection_bp.route('/health', methods=['GET'])
def collection_health():
    """Check collection service health"""
    try:
        stats = collection_service.get_collection_stats()
        return jsonify({
            'status': 'healthy',
            'data': stats
        }), 200
    except Exception as e:
        logger.error(f"Collection health check failed: {e}")
        return jsonify({'error': 'Collection service unavailable'}), 500

@collection_bp.route('/influencers', methods=['POST'])
@jwt_required()
def create_influencer():
    """Create a new influencer for tracking"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('platform'):
            return jsonify({'error': 'Username and platform are required'}), 400
        
        # Check if platform is valid
        try:
            platform = Platform(data['platform'].lower())
        except ValueError:
            return jsonify({'error': 'Invalid platform'}), 400
        
        # Check if influencer already exists
        existing = Influencer.query.filter_by(
            username=data['username'],
            platform=platform
        ).first()
        
        if existing:
            return jsonify({'error': 'Influencer already exists'}), 409
        
        # Create new influencer
        influencer = Influencer(
            external_id=data.get('external_id', data['username']),
            username=data['username'],
            display_name=data.get('display_name', ''),
            platform=platform,
            bio=data.get('bio', ''),
            priority_score=data.get('priority_score', 1.0)
        )
        
        db.session.add(influencer)
        db.session.commit()
        
        # Schedule initial collection
        tasks = asyncio.run(collection_service.schedule_collection_for_influencer(
            influencer.id, 
            TaskPriority.HIGH
        ))
        
        logger.info(f"Created influencer {influencer.username} with {len(tasks)} collection tasks")
        
        return jsonify({
            'message': 'Influencer created successfully',
            'influencer': influencer.to_dict(),
            'scheduled_tasks': len(tasks)
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating influencer: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create influencer'}), 500

@collection_bp.route('/influencers', methods=['GET'])
@jwt_required()
def list_influencers():
    """List all tracked influencers"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        platform = request.args.get('platform')
        
        query = Influencer.query
        
        if platform:
            try:
                platform_enum = Platform(platform.lower())
                query = query.filter_by(platform=platform_enum)
            except ValueError:
                return jsonify({'error': 'Invalid platform'}), 400
        
        paginated = query.order_by(Influencer.follower_count.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'influencers': [influencer.to_dict(include_analytics=True) 
                          for influencer in paginated.items],
            'pagination': {
                'page': page,
                'pages': paginated.pages,
                'per_page': per_page,
                'total': paginated.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing influencers: {e}")
        return jsonify({'error': 'Failed to retrieve influencers'}), 500

@collection_bp.route('/influencers/<int:influencer_id>/collect', methods=['POST'])
@jwt_required()
def collect_influencer_data(influencer_id):
    """Trigger data collection for a specific influencer"""
    try:
        data = request.get_json() or {}
        force = data.get('force', False)
        include_posts = data.get('include_posts', True)
        posts_limit = data.get('posts_limit', 50)
        
        # Check if influencer exists
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        results = []
        
        # Collect profile data
        profile_result = asyncio.run(
            collection_service.collect_influencer_profile(influencer_id, force=force)
        )
        results.append({
            'type': 'profile',
            'success': profile_result.success,
            'items_collected': profile_result.items_collected,
            'error': profile_result.error
        })
        
        # Collect posts if requested
        if include_posts and profile_result.success:
            posts_result = asyncio.run(
                collection_service.collect_influencer_posts(
                    influencer_id, limit=posts_limit, force=force
                )
            )
            results.append({
                'type': 'posts',
                'success': posts_result.success,
                'items_collected': posts_result.items_collected,
                'error': posts_result.error
            })
        
        overall_success = all(result['success'] for result in results)
        
        return jsonify({
            'success': overall_success,
            'message': f'Collection {"completed" if overall_success else "partially failed"}',
            'results': results
        }), 200 if overall_success else 207
        
    except Exception as e:
        logger.error(f"Error collecting influencer data: {e}")
        return jsonify({'error': 'Collection failed'}), 500

@collection_bp.route('/posts/<int:post_id>/comments/collect', methods=['POST'])
@jwt_required()
def collect_post_comments(post_id):
    """Collect comments for a specific post"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 100)
        
        result = asyncio.run(
            collection_service.collect_post_comments(post_id, limit=limit)
        )
        
        return jsonify({
            'success': result.success,
            'items_collected': result.items_collected,
            'error': result.error,
            'data': result.data if result.success else None
        }), 200 if result.success else 400
        
    except Exception as e:
        logger.error(f"Error collecting post comments: {e}")
        return jsonify({'error': 'Comment collection failed'}), 500

@collection_bp.route('/tasks', methods=['GET'])
@jwt_required()
def list_collection_tasks():
    """List collection tasks with filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status')
        platform = request.args.get('platform')
        influencer_id = request.args.get('influencer_id', type=int)
        
        query = CollectionTask.query
        
        if status:
            try:
                status_enum = TaskStatus(status.lower())
                query = query.filter_by(status=status_enum)
            except ValueError:
                return jsonify({'error': 'Invalid status'}), 400
        
        if platform:
            try:
                platform_enum = Platform(platform.lower())
                query = query.filter_by(platform=platform_enum)
            except ValueError:
                return jsonify({'error': 'Invalid platform'}), 400
        
        if influencer_id:
            query = query.filter_by(influencer_id=influencer_id)
        
        paginated = query.order_by(CollectionTask.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'tasks': [task.to_dict() for task in paginated.items],
            'pagination': {
                'page': page,
                'pages': paginated.pages,
                'per_page': per_page,
                'total': paginated.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing collection tasks: {e}")
        return jsonify({'error': 'Failed to retrieve tasks'}), 500

@collection_bp.route('/tasks/process', methods=['POST'])
@jwt_required()
def process_pending_tasks():
    """Process pending collection tasks"""
    try:
        data = request.get_json() or {}
        max_tasks = data.get('max_tasks', 10)
        
        processed_count = asyncio.run(
            collection_service.process_pending_tasks(max_tasks=max_tasks)
        )
        
        return jsonify({
            'message': f'Processed {processed_count} tasks',
            'processed_count': processed_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing pending tasks: {e}")
        return jsonify({'error': 'Task processing failed'}), 500

@collection_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_collection_statistics():
    """Get collection service statistics"""
    try:
        stats = collection_service.get_collection_stats()
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting collection stats: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500

@collection_bp.route('/schedule', methods=['POST'])
@jwt_required()
def schedule_collection():
    """Schedule collection for multiple influencers"""
    try:
        data = request.get_json()
        influencer_ids = data.get('influencer_ids', [])
        priority = data.get('priority', 'normal')
        
        if not influencer_ids:
            return jsonify({'error': 'No influencer IDs provided'}), 400
        
        try:
            priority_enum = TaskPriority[priority.upper()]
        except KeyError:
            return jsonify({'error': 'Invalid priority level'}), 400
        
        total_tasks = 0
        results = []
        
        for influencer_id in influencer_ids:
            try:
                tasks = asyncio.run(
                    collection_service.schedule_collection_for_influencer(
                        influencer_id, priority_enum
                    )
                )
                total_tasks += len(tasks)
                results.append({
                    'influencer_id': influencer_id,
                    'scheduled_tasks': len(tasks),
                    'success': True
                })
            except Exception as e:
                logger.error(f"Error scheduling collection for influencer {influencer_id}: {e}")
                results.append({
                    'influencer_id': influencer_id,
                    'scheduled_tasks': 0,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'message': f'Scheduled {total_tasks} total tasks',
            'total_tasks': total_tasks,
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error scheduling collection: {e}")
        return jsonify({'error': 'Failed to schedule collection'}), 500