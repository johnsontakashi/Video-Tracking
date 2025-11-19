from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSON, UUID
import uuid
from app import db

class Platform(Enum):
    """Social media platforms"""
    INSTAGRAM = "instagram"
    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    TWITTER = "twitter"

class InfluencerStatus(Enum):
    """Influencer status for collection tracking"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    COLLECTING = "collecting"
    ERROR = "error"

class Influencer(db.Model):
    """Enhanced influencer model with comprehensive tracking"""
    
    __tablename__ = 'influencers'
    
    id = db.Column(db.BigInteger, primary_key=True)
    external_id = db.Column(db.String(100), nullable=False, index=True)  # Platform-specific ID
    username = db.Column(db.String(100), nullable=False, index=True)
    display_name = db.Column(db.String(255))
    platform = db.Column(db.Enum(Platform), nullable=False, index=True)
    
    # Profile information
    bio = db.Column(db.Text)
    profile_image_url = db.Column(db.String(500))
    profile_url = db.Column(db.String(500))
    verified = db.Column(db.Boolean, default=False)
    business_account = db.Column(db.Boolean, default=False)
    
    # Metrics
    follower_count = db.Column(db.BigInteger, default=0, index=True)
    following_count = db.Column(db.BigInteger, default=0)
    post_count = db.Column(db.BigInteger, default=0)
    
    # Location data
    location = db.Column(db.String(255))
    country_code = db.Column(db.String(10))
    language_code = db.Column(db.String(10))
    
    # Collection metadata
    status = db.Column(db.Enum(InfluencerStatus), default=InfluencerStatus.ACTIVE, index=True)
    last_collected = db.Column(db.DateTime)
    collection_frequency = db.Column(db.Integer, default=24)  # Hours between collections
    priority_score = db.Column(db.Float, default=1.0)  # Collection priority
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='influencer', cascade='all, delete-orphan')
    analytics = db.relationship('InfluencerAnalytics', backref='influencer', cascade='all, delete-orphan')
    collections = db.relationship('CollectionTask', backref='influencer', cascade='all, delete-orphan')
    
    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('external_id', 'platform', name='uq_influencer_platform'),
        db.Index('idx_influencer_followers_platform', 'follower_count', 'platform'),
        db.Index('idx_influencer_updated', 'updated_at'),
    )
    
    def __repr__(self):
        return f'<Influencer {self.username}@{self.platform.value}>'
    
    @property
    def engagement_rate(self):
        """Calculate current engagement rate"""
        if not self.follower_count:
            return 0.0
        
        # Get recent posts average engagement
        recent_analytics = InfluencerAnalytics.query.filter_by(
            influencer_id=self.id
        ).order_by(InfluencerAnalytics.computed_at.desc()).first()
        
        return recent_analytics.engagement_rate if recent_analytics else 0.0
    
    def needs_collection(self) -> bool:
        """Check if influencer needs data collection"""
        if not self.last_collected:
            return True
            
        hours_since_last = (datetime.utcnow() - self.last_collected).total_seconds() / 3600
        return hours_since_last >= self.collection_frequency
    
    def to_dict(self, include_analytics=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'external_id': self.external_id,
            'username': self.username,
            'display_name': self.display_name,
            'platform': self.platform.value,
            'bio': self.bio,
            'profile_image_url': self.profile_image_url,
            'profile_url': self.profile_url,
            'verified': self.verified,
            'business_account': self.business_account,
            'follower_count': self.follower_count,
            'following_count': self.following_count,
            'post_count': self.post_count,
            'location': self.location,
            'country_code': self.country_code,
            'language_code': self.language_code,
            'status': self.status.value,
            'last_collected': self.last_collected.isoformat() if self.last_collected else None,
            'engagement_rate': self.engagement_rate,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_analytics:
            # Get latest analytics
            latest_analytics = InfluencerAnalytics.query.filter_by(
                influencer_id=self.id
            ).order_by(InfluencerAnalytics.computed_at.desc()).first()
            
            if latest_analytics:
                data['analytics'] = latest_analytics.to_dict()
        
        return data

class Post(db.Model):
    """Enhanced post model with comprehensive data"""
    
    __tablename__ = 'posts'
    
    id = db.Column(db.BigInteger, primary_key=True)
    external_id = db.Column(db.String(100), nullable=False, index=True)  # Platform post ID
    influencer_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    platform = db.Column(db.Enum(Platform), nullable=False, index=True)
    
    # Content
    content = db.Column(db.Text)
    content_type = db.Column(db.String(50))  # photo, video, story, reel, etc.
    media_urls = db.Column(JSON)  # Array of media URLs
    hashtags = db.Column(JSON)  # Array of hashtags
    mentions = db.Column(JSON)  # Array of mentions
    
    # Metrics
    likes_count = db.Column(db.BigInteger, default=0)
    comments_count = db.Column(db.BigInteger, default=0)
    shares_count = db.Column(db.BigInteger, default=0)
    views_count = db.Column(db.BigInteger, default=0)
    
    # Metadata
    posted_at = db.Column(db.DateTime, nullable=False, index=True)
    language_detected = db.Column(db.String(10))
    location_data = db.Column(JSON)  # Location information if available
    
    # Raw data storage
    raw_data = db.Column(JSON)  # Store complete platform response
    
    # Timestamps
    collected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan')
    sentiments = db.relationship('PostSentiment', backref='post', cascade='all, delete-orphan')
    
    # Table configuration
    __table_args__ = (
        db.UniqueConstraint('external_id', 'platform', name='uq_post_platform'),
        db.Index('idx_post_influencer_date', 'influencer_id', 'posted_at'),
        db.Index('idx_post_engagement', 'likes_count', 'comments_count'),
        # Partition by posted_at (would be implemented in migration)
    )
    
    def __repr__(self):
        return f'<Post {self.external_id}@{self.platform.value}>'
    
    @property
    def engagement_rate(self):
        """Calculate engagement rate for this post"""
        total_engagement = (self.likes_count or 0) + (self.comments_count or 0) + (self.shares_count or 0)
        if self.influencer and self.influencer.follower_count:
            return (total_engagement / self.influencer.follower_count) * 100
        return 0.0
    
    @property
    def sentiment_score(self):
        """Get overall sentiment score"""
        sentiment = PostSentiment.query.filter_by(post_id=self.id).first()
        return sentiment.compound_score if sentiment else 0.0
    
    def to_dict(self, include_comments=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'external_id': self.external_id,
            'platform': self.platform.value,
            'content': self.content,
            'content_type': self.content_type,
            'media_urls': self.media_urls,
            'hashtags': self.hashtags,
            'mentions': self.mentions,
            'likes_count': self.likes_count,
            'comments_count': self.comments_count,
            'shares_count': self.shares_count,
            'views_count': self.views_count,
            'engagement_rate': self.engagement_rate,
            'posted_at': self.posted_at.isoformat(),
            'language_detected': self.language_detected,
            'location_data': self.location_data,
            'sentiment_score': self.sentiment_score,
            'collected_at': self.collected_at.isoformat()
        }
        
        if include_comments:
            data['comments'] = [comment.to_dict() for comment in self.comments[:10]]  # Limit to 10
        
        return data

class Comment(db.Model):
    """Comment model for posts"""
    
    __tablename__ = 'comments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    external_id = db.Column(db.String(100), nullable=False)
    post_id = db.Column(db.BigInteger, db.ForeignKey('posts.id'), nullable=False, index=True)
    
    # Content
    content = db.Column(db.Text, nullable=False)
    author_username = db.Column(db.String(100))
    author_display_name = db.Column(db.String(255))
    
    # Metrics
    likes_count = db.Column(db.Integer, default=0)
    replies_count = db.Column(db.Integer, default=0)
    
    # Metadata
    posted_at = db.Column(db.DateTime, nullable=False)
    language_detected = db.Column(db.String(10))
    
    # Timestamps
    collected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    sentiment = db.relationship('CommentSentiment', backref='comment', uselist=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_comment_post_date', 'post_id', 'posted_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'external_id': self.external_id,
            'content': self.content,
            'author_username': self.author_username,
            'author_display_name': self.author_display_name,
            'likes_count': self.likes_count,
            'replies_count': self.replies_count,
            'posted_at': self.posted_at.isoformat(),
            'language_detected': self.language_detected,
            'sentiment_score': self.sentiment.compound_score if self.sentiment else 0.0
        }

class InfluencerAnalytics(db.Model):
    """Analytics data for influencers"""
    
    __tablename__ = 'influencer_analytics'
    
    id = db.Column(db.BigInteger, primary_key=True)
    influencer_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    
    # Computed scores
    influence_score = db.Column(db.Float, nullable=False, index=True)  # 0-100
    engagement_rate = db.Column(db.Float, default=0.0)  # Percentage
    consistency_score = db.Column(db.Float, default=0.0)  # Posting consistency
    growth_rate = db.Column(db.Float, default=0.0)  # Follower growth rate
    
    # Sentiment analytics
    sentiment_positive = db.Column(db.Float, default=0.0)
    sentiment_neutral = db.Column(db.Float, default=0.0)
    sentiment_negative = db.Column(db.Float, default=0.0)
    sentiment_compound = db.Column(db.Float, default=0.0)
    
    # Content analytics
    avg_likes = db.Column(db.Float, default=0.0)
    avg_comments = db.Column(db.Float, default=0.0)
    avg_shares = db.Column(db.Float, default=0.0)
    top_hashtags = db.Column(JSON)  # Most used hashtags
    top_keywords = db.Column(JSON)  # Extracted keywords
    
    # Time period for analytics
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    posts_analyzed = db.Column(db.Integer, default=0)
    
    # Metadata
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Table configuration
    __table_args__ = (
        db.Index('idx_analytics_influencer_date', 'influencer_id', 'computed_at'),
        db.Index('idx_analytics_score_date', 'influence_score', 'computed_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'influence_score': self.influence_score,
            'engagement_rate': self.engagement_rate,
            'consistency_score': self.consistency_score,
            'growth_rate': self.growth_rate,
            'sentiment': {
                'positive': self.sentiment_positive,
                'neutral': self.sentiment_neutral,
                'negative': self.sentiment_negative,
                'compound': self.sentiment_compound
            },
            'content_metrics': {
                'avg_likes': self.avg_likes,
                'avg_comments': self.avg_comments,
                'avg_shares': self.avg_shares
            },
            'top_hashtags': self.top_hashtags,
            'top_keywords': self.top_keywords,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'posts_analyzed': self.posts_analyzed,
            'computed_at': self.computed_at.isoformat()
        }