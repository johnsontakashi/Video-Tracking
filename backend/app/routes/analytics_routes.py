from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import asyncio
import logging
from datetime import datetime, timedelta

from app.services.analytics_service import AnalyticsService
from app.models.influencer import Influencer, Post, Comment, InfluencerAnalytics
from app.models.analytics import (
    PostSentiment, CommentSentiment, SentimentLabel, 
    TrendingTopic, KeywordAnalysis, InfluenceScoreHistory
)
from app import db

logger = logging.getLogger(__name__)

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

# Initialize analytics service
analytics_service = AnalyticsService()

@analytics_bp.route('/health', methods=['GET'])
def analytics_health():
    """Check analytics service health"""
    try:
        summary = analytics_service.get_analytics_summary()
        return jsonify({
            'status': 'healthy',
            'data': summary
        }), 200
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return jsonify({'error': 'Analytics service unavailable'}), 500

@analytics_bp.route('/influencer/<int:influencer_id>/analyze', methods=['POST'])
@jwt_required()
def analyze_influencer(influencer_id):
    """Analyze influencer and calculate comprehensive analytics"""
    try:
        data = request.get_json() or {}
        days_back = data.get('days_back', 30)
        
        # Check if influencer exists
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        # Calculate analytics
        analytics = asyncio.run(
            analytics_service.calculate_influencer_analytics(influencer, days_back)
        )
        
        if analytics:
            return jsonify({
                'success': True,
                'message': 'Analytics calculated successfully',
                'analytics': analytics.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to calculate analytics'
            }), 400
            
    except Exception as e:
        logger.error(f"Error analyzing influencer {influencer_id}: {e}")
        return jsonify({'error': 'Analytics calculation failed'}), 500

@analytics_bp.route('/sentiment/posts/<int:post_id>', methods=['POST'])
@jwt_required()
def analyze_post_sentiment(post_id):
    """Analyze sentiment for a specific post"""
    try:
        post = Post.query.get(post_id)
        if not post:
            return jsonify({'error': 'Post not found'}), 404
        
        sentiment = asyncio.run(analytics_service.analyze_post_sentiment(post))
        
        if sentiment:
            return jsonify({
                'success': True,
                'sentiment': sentiment.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to analyze sentiment'
            }), 400
            
    except Exception as e:
        logger.error(f"Error analyzing post sentiment: {e}")
        return jsonify({'error': 'Sentiment analysis failed'}), 500

@analytics_bp.route('/sentiment/comments/<int:comment_id>', methods=['POST'])
@jwt_required()
def analyze_comment_sentiment(comment_id):
    """Analyze sentiment for a specific comment"""
    try:
        comment = Comment.query.get(comment_id)
        if not comment:
            return jsonify({'error': 'Comment not found'}), 404
        
        sentiment = asyncio.run(analytics_service.analyze_comment_sentiment(comment))
        
        if sentiment:
            return jsonify({
                'success': True,
                'sentiment': sentiment.to_dict()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to analyze sentiment'
            }), 400
            
    except Exception as e:
        logger.error(f"Error analyzing comment sentiment: {e}")
        return jsonify({'error': 'Sentiment analysis failed'}), 500

@analytics_bp.route('/sentiment/bulk', methods=['POST'])
@jwt_required()
def bulk_sentiment_analysis():
    """Process sentiment analysis for posts without analysis"""
    try:
        data = request.get_json() or {}
        batch_size = min(data.get('batch_size', 100), 500)
        
        processed_count = asyncio.run(
            analytics_service.process_bulk_sentiment_analysis(batch_size)
        )
        
        return jsonify({
            'success': True,
            'message': f'Processed {processed_count} posts',
            'processed_count': processed_count
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk sentiment analysis: {e}")
        return jsonify({'error': 'Bulk sentiment analysis failed'}), 500

@analytics_bp.route('/trending', methods=['GET'])
@jwt_required()
def get_trending_topics():
    """Get current trending topics"""
    try:
        hours_back = request.args.get('hours_back', 24, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # Get trending topics from database
        trending_topics = TrendingTopic.query.filter_by(
            is_active=True
        ).order_by(
            TrendingTopic.velocity.desc()
        ).limit(limit).all()
        
        return jsonify({
            'trending_topics': [topic.to_dict() for topic in trending_topics],
            'analysis_period_hours': hours_back
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting trending topics: {e}")
        return jsonify({'error': 'Failed to retrieve trending topics'}), 500

@analytics_bp.route('/trending/detect', methods=['POST'])
@jwt_required()
def detect_trending_topics():
    """Detect new trending topics"""
    try:
        data = request.get_json() or {}
        hours_back = data.get('hours_back', 24)
        
        trending_topics = asyncio.run(
            analytics_service.detect_trending_topics(hours_back)
        )
        
        return jsonify({
            'success': True,
            'message': f'Detected {len(trending_topics)} trending topics',
            'trending_topics': [topic.to_dict() for topic in trending_topics]
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting trending topics: {e}")
        return jsonify({'error': 'Trending topic detection failed'}), 500

@analytics_bp.route('/influencer/<int:influencer_id>/analytics', methods=['GET'])
@jwt_required()
def get_influencer_analytics(influencer_id):
    """Get analytics for a specific influencer"""
    try:
        # Check if influencer exists
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        # Get latest analytics
        latest_analytics = InfluencerAnalytics.query.filter_by(
            influencer_id=influencer_id
        ).order_by(InfluencerAnalytics.computed_at.desc()).first()
        
        # Get analytics history
        analytics_history = InfluencerAnalytics.query.filter_by(
            influencer_id=influencer_id
        ).order_by(InfluencerAnalytics.computed_at.desc()).limit(10).all()
        
        # Get influence score history
        score_history = InfluenceScoreHistory.query.filter_by(
            influencer_id=influencer_id
        ).order_by(InfluenceScoreHistory.computed_at.desc()).limit(30).all()
        
        return jsonify({
            'influencer': influencer.to_dict(),
            'latest_analytics': latest_analytics.to_dict() if latest_analytics else None,
            'analytics_history': [a.to_dict() for a in analytics_history],
            'score_history': [s.to_dict() for s in score_history]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting influencer analytics: {e}")
        return jsonify({'error': 'Failed to retrieve analytics'}), 500

@analytics_bp.route('/leaderboard', methods=['GET'])
@jwt_required()
def get_influence_leaderboard():
    """Get top influencers by influence score"""
    try:
        platform = request.args.get('platform')
        limit = min(request.args.get('limit', 50, type=int), 100)
        days_back = request.args.get('days_back', 7, type=int)
        
        # Get cutoff date for recent analytics
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Build query for latest analytics per influencer
        query = db.session.query(InfluencerAnalytics).join(Influencer).filter(
            InfluencerAnalytics.computed_at >= cutoff_date
        )
        
        if platform:
            from app.models.influencer import Platform
            try:
                platform_enum = Platform(platform.lower())
                query = query.filter(Influencer.platform == platform_enum)
            except ValueError:
                return jsonify({'error': 'Invalid platform'}), 400
        
        # Get the latest analytics for each influencer
        subquery = query.order_by(
            InfluencerAnalytics.influencer_id,
            InfluencerAnalytics.computed_at.desc()
        ).distinct(InfluencerAnalytics.influencer_id).subquery()
        
        leaderboard_query = db.session.query(InfluencerAnalytics).join(
            subquery, InfluencerAnalytics.id == subquery.c.id
        ).join(Influencer).order_by(
            InfluencerAnalytics.influence_score.desc()
        ).limit(limit)
        
        leaderboard = []
        for i, analytics in enumerate(leaderboard_query.all(), 1):
            leaderboard.append({
                'rank': i,
                'influencer': analytics.influencer.to_dict(),
                'analytics': analytics.to_dict()
            })
        
        return jsonify({
            'leaderboard': leaderboard,
            'filters': {
                'platform': platform,
                'days_back': days_back,
                'limit': limit
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting influence leaderboard: {e}")
        return jsonify({'error': 'Failed to retrieve leaderboard'}), 500

@analytics_bp.route('/sentiment/overview', methods=['GET'])
@jwt_required()
def get_sentiment_overview():
    """Get sentiment analysis overview"""
    try:
        days_back = request.args.get('days_back', 7, type=int)
        platform = request.args.get('platform')
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Build base query
        query = db.session.query(PostSentiment).join(Post).filter(
            PostSentiment.analyzed_at >= cutoff_date
        )
        
        if platform:
            from app.models.influencer import Platform
            try:
                platform_enum = Platform(platform.lower())
                query = query.filter(Post.platform == platform_enum)
            except ValueError:
                return jsonify({'error': 'Invalid platform'}), 400
        
        # Get sentiment distribution
        sentiment_counts = {}
        for label in SentimentLabel:
            count = query.filter(PostSentiment.label == label).count()
            sentiment_counts[label.value] = count
        
        # Get average sentiment scores
        avg_scores = query.with_entities(
            db.func.avg(PostSentiment.positive_score).label('avg_positive'),
            db.func.avg(PostSentiment.neutral_score).label('avg_neutral'),
            db.func.avg(PostSentiment.negative_score).label('avg_negative'),
            db.func.avg(PostSentiment.compound_score).label('avg_compound')
        ).first()
        
        # Get daily sentiment trends
        daily_sentiment = query.with_entities(
            db.func.date(PostSentiment.analyzed_at).label('date'),
            db.func.avg(PostSentiment.compound_score).label('avg_compound'),
            db.func.count().label('post_count')
        ).group_by(
            db.func.date(PostSentiment.analyzed_at)
        ).order_by('date').all()
        
        return jsonify({
            'sentiment_distribution': sentiment_counts,
            'average_scores': {
                'positive': float(avg_scores.avg_positive or 0),
                'neutral': float(avg_scores.avg_neutral or 0),
                'negative': float(avg_scores.avg_negative or 0),
                'compound': float(avg_scores.avg_compound or 0)
            },
            'daily_trends': [
                {
                    'date': trend.date.isoformat(),
                    'avg_compound': float(trend.avg_compound),
                    'post_count': trend.post_count
                } for trend in daily_sentiment
            ],
            'analysis_period_days': days_back,
            'platform_filter': platform
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting sentiment overview: {e}")
        return jsonify({'error': 'Failed to retrieve sentiment overview'}), 500

@analytics_bp.route('/keywords/<int:influencer_id>', methods=['GET'])
@jwt_required()
def get_influencer_keywords(influencer_id):
    """Get keyword analysis for an influencer"""
    try:
        # Check if influencer exists
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        # Get latest keyword analysis
        keyword_analysis = KeywordAnalysis.query.filter_by(
            influencer_id=influencer_id
        ).order_by(KeywordAnalysis.computed_at.desc()).first()
        
        if keyword_analysis:
            return jsonify({
                'influencer': influencer.to_dict(),
                'keyword_analysis': keyword_analysis.to_dict()
            }), 200
        else:
            return jsonify({
                'influencer': influencer.to_dict(),
                'keyword_analysis': None,
                'message': 'No keyword analysis available'
            }), 200
        
    except Exception as e:
        logger.error(f"Error getting influencer keywords: {e}")
        return jsonify({'error': 'Failed to retrieve keyword analysis'}), 500

@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        # Get summary statistics
        summary = analytics_service.get_analytics_summary()
        
        # Get recent trending topics
        trending_topics = TrendingTopic.query.filter_by(
            is_active=True
        ).order_by(TrendingTopic.velocity.desc()).limit(10).all()
        
        # Get top performers (by influence score)
        top_performers = db.session.query(InfluencerAnalytics).join(Influencer).order_by(
            InfluencerAnalytics.influence_score.desc()
        ).limit(10).all()
        
        # Get recent sentiment trends
        recent_sentiment = db.session.query(PostSentiment).filter(
            PostSentiment.analyzed_at >= datetime.utcnow() - timedelta(days=7)
        ).all()
        
        sentiment_by_day = {}
        for sentiment in recent_sentiment:
            day = sentiment.analyzed_at.date()
            if day not in sentiment_by_day:
                sentiment_by_day[day] = {'positive': 0, 'neutral': 0, 'negative': 0, 'mixed': 0}
            sentiment_by_day[day][sentiment.label.value] += 1
        
        return jsonify({
            'summary': summary,
            'trending_topics': [topic.to_dict() for topic in trending_topics],
            'top_performers': [
                {
                    'influencer': performer.influencer.to_dict(),
                    'analytics': performer.to_dict()
                } for performer in top_performers
            ],
            'sentiment_trends': [
                {
                    'date': date.isoformat(),
                    'counts': counts
                } for date, counts in sorted(sentiment_by_day.items())
            ]
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting analytics dashboard: {e}")
        return jsonify({'error': 'Failed to retrieve dashboard data'}), 500

@analytics_bp.route('/export/<int:influencer_id>', methods=['GET'])
@jwt_required()
def export_influencer_analytics(influencer_id):
    """Export influencer analytics data"""
    try:
        format_type = request.args.get('format', 'json').lower()
        days_back = request.args.get('days_back', 30, type=int)
        
        # Check if influencer exists
        influencer = Influencer.query.get(influencer_id)
        if not influencer:
            return jsonify({'error': 'Influencer not found'}), 404
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # Get comprehensive data
        analytics_data = {
            'influencer': influencer.to_dict(include_analytics=True),
            'analytics_history': [
                a.to_dict() for a in InfluencerAnalytics.query.filter(
                    InfluencerAnalytics.influencer_id == influencer_id,
                    InfluencerAnalytics.computed_at >= cutoff_date
                ).order_by(InfluencerAnalytics.computed_at.desc()).all()
            ],
            'score_history': [
                s.to_dict() for s in InfluenceScoreHistory.query.filter(
                    InfluenceScoreHistory.influencer_id == influencer_id,
                    InfluenceScoreHistory.computed_at >= cutoff_date
                ).order_by(InfluenceScoreHistory.computed_at.desc()).all()
            ],
            'export_metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'period_days': days_back,
                'format': format_type
            }
        }
        
        if format_type == 'json':
            return jsonify(analytics_data), 200
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
        
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        return jsonify({'error': 'Failed to export analytics'}), 500