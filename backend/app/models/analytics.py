from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSON
from app import db

class SentimentLabel(Enum):
    """Sentiment classification labels"""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    MIXED = "mixed"

class PostSentiment(db.Model):
    """Sentiment analysis for posts"""
    
    __tablename__ = 'post_sentiments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    post_id = db.Column(db.BigInteger, db.ForeignKey('posts.id'), nullable=False, unique=True, index=True)
    
    # Sentiment scores
    positive_score = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    neutral_score = db.Column(db.Float, nullable=False)
    negative_score = db.Column(db.Float, nullable=False)
    compound_score = db.Column(db.Float, nullable=False)  # -1.0 to 1.0
    
    # Classification
    label = db.Column(db.Enum(SentimentLabel), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    
    # Language and model info
    language_detected = db.Column(db.String(10), nullable=False)
    model_version = db.Column(db.String(50))
    
    # Keywords and entities
    keywords_positive = db.Column(JSON)  # Positive keywords found
    keywords_negative = db.Column(JSON)  # Negative keywords found
    entities_mentioned = db.Column(JSON)  # Named entities (brands, people, etc.)
    
    # Timestamp
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<PostSentiment {self.label.value}: {self.compound_score:.3f}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'post_id': self.post_id,
            'scores': {
                'positive': self.positive_score,
                'neutral': self.neutral_score,
                'negative': self.negative_score,
                'compound': self.compound_score
            },
            'label': self.label.value,
            'confidence': self.confidence,
            'language_detected': self.language_detected,
            'keywords': {
                'positive': self.keywords_positive,
                'negative': self.keywords_negative
            },
            'entities_mentioned': self.entities_mentioned,
            'analyzed_at': self.analyzed_at.isoformat()
        }

class CommentSentiment(db.Model):
    """Sentiment analysis for comments"""
    
    __tablename__ = 'comment_sentiments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    comment_id = db.Column(db.BigInteger, db.ForeignKey('comments.id'), nullable=False, unique=True, index=True)
    
    # Sentiment scores
    positive_score = db.Column(db.Float, nullable=False)
    neutral_score = db.Column(db.Float, nullable=False)
    negative_score = db.Column(db.Float, nullable=False)
    compound_score = db.Column(db.Float, nullable=False)
    
    # Classification
    label = db.Column(db.Enum(SentimentLabel), nullable=False, index=True)
    confidence = db.Column(db.Float, nullable=False)
    
    # Language and processing
    language_detected = db.Column(db.String(10), nullable=False)
    is_spam = db.Column(db.Boolean, default=False)  # Spam detection
    
    # Timestamp
    analyzed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'comment_id': self.comment_id,
            'scores': {
                'positive': self.positive_score,
                'neutral': self.neutral_score,
                'negative': self.negative_score,
                'compound': self.compound_score
            },
            'label': self.label.value,
            'confidence': self.confidence,
            'language_detected': self.language_detected,
            'is_spam': self.is_spam,
            'analyzed_at': self.analyzed_at.isoformat()
        }

class TrendingTopic(db.Model):
    """Trending topics detection"""
    
    __tablename__ = 'trending_topics'
    
    id = db.Column(db.BigInteger, primary_key=True)
    
    # Topic information
    topic = db.Column(db.String(255), nullable=False, index=True)
    hashtag = db.Column(db.String(100))  # If topic is a hashtag
    category = db.Column(db.String(100))  # Technology, Fashion, Sports, etc.
    
    # Trend metrics
    mention_count = db.Column(db.Integer, default=0)
    growth_rate = db.Column(db.Float, default=0.0)  # Percentage growth
    velocity = db.Column(db.Float, default=0.0)  # Mentions per hour
    peak_mentions = db.Column(db.Integer, default=0)
    
    # Geographic data
    countries = db.Column(JSON)  # Countries where trending
    languages = db.Column(JSON)  # Languages used
    
    # Sentiment for topic
    sentiment_positive = db.Column(db.Float, default=0.0)
    sentiment_neutral = db.Column(db.Float, default=0.0)
    sentiment_negative = db.Column(db.Float, default=0.0)
    
    # Time tracking
    detected_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    trending_since = db.Column(db.DateTime, nullable=False)
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Related data
    related_topics = db.Column(JSON)  # Related trending topics
    top_posts = db.Column(JSON)  # Top posts for this topic
    influencers_discussing = db.Column(JSON)  # Top influencers discussing
    
    # Indexes
    __table_args__ = (
        db.Index('idx_trending_topic_date', 'topic', 'detected_at'),
        db.Index('idx_trending_active', 'is_active', 'last_updated'),
        db.Index('idx_trending_velocity', 'velocity'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'topic': self.topic,
            'hashtag': self.hashtag,
            'category': self.category,
            'metrics': {
                'mention_count': self.mention_count,
                'growth_rate': self.growth_rate,
                'velocity': self.velocity,
                'peak_mentions': self.peak_mentions
            },
            'geographic': {
                'countries': self.countries,
                'languages': self.languages
            },
            'sentiment': {
                'positive': self.sentiment_positive,
                'neutral': self.sentiment_neutral,
                'negative': self.sentiment_negative
            },
            'detected_at': self.detected_at.isoformat(),
            'trending_since': self.trending_since.isoformat(),
            'is_active': self.is_active,
            'related_topics': self.related_topics,
            'influencers_discussing': self.influencers_discussing
        }

class KeywordAnalysis(db.Model):
    """Keyword analysis and extraction"""
    
    __tablename__ = 'keyword_analysis'
    
    id = db.Column(db.BigInteger, primary_key=True)
    influencer_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    
    # Time period
    analysis_period_start = db.Column(db.DateTime, nullable=False)
    analysis_period_end = db.Column(db.DateTime, nullable=False)
    
    # Keyword data
    top_keywords = db.Column(JSON, nullable=False)  # [{keyword, score, frequency}]
    hashtags = db.Column(JSON)  # Top hashtags used
    mentions = db.Column(JSON)  # Top @mentions
    
    # TF-IDF scores
    tfidf_keywords = db.Column(JSON)  # TF-IDF weighted keywords
    
    # Topic modeling
    topics = db.Column(JSON)  # LDA topics
    topic_distribution = db.Column(JSON)  # Topic probability distribution
    
    # Language analysis
    language_distribution = db.Column(JSON)  # Languages used
    
    # Metadata
    posts_analyzed = db.Column(db.Integer, default=0)
    model_version = db.Column(db.String(50))
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_keyword_influencer_date', 'influencer_id', 'computed_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'influencer_id': self.influencer_id,
            'period_start': self.analysis_period_start.isoformat(),
            'period_end': self.analysis_period_end.isoformat(),
            'keywords': {
                'top_keywords': self.top_keywords,
                'hashtags': self.hashtags,
                'mentions': self.mentions,
                'tfidf_keywords': self.tfidf_keywords
            },
            'topics': {
                'topics': self.topics,
                'distribution': self.topic_distribution
            },
            'language_distribution': self.language_distribution,
            'posts_analyzed': self.posts_analyzed,
            'computed_at': self.computed_at.isoformat()
        }

class InfluenceScoreHistory(db.Model):
    """Historical influence scores for tracking"""
    
    __tablename__ = 'influence_score_history'
    
    id = db.Column(db.BigInteger, primary_key=True)
    influencer_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    
    # Score components
    influence_score = db.Column(db.Float, nullable=False)
    content_quality_score = db.Column(db.Float, nullable=False)
    engagement_score = db.Column(db.Float, nullable=False)
    reach_score = db.Column(db.Float, nullable=False)
    authenticity_score = db.Column(db.Float, nullable=False)
    consistency_score = db.Column(db.Float, nullable=False)
    
    # Contributing factors
    follower_count = db.Column(db.BigInteger)
    engagement_rate = db.Column(db.Float)
    posting_frequency = db.Column(db.Float)
    sentiment_score = db.Column(db.Float)
    
    # Change tracking
    score_change = db.Column(db.Float, default=0.0)  # Change from previous score
    rank_change = db.Column(db.Integer, default=0)  # Rank change
    
    # Metadata
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    computation_version = db.Column(db.String(20))
    
    # Indexes
    __table_args__ = (
        db.Index('idx_score_history_influencer_date', 'influencer_id', 'computed_at'),
        db.Index('idx_score_history_score', 'influence_score', 'computed_at'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'influencer_id': self.influencer_id,
            'scores': {
                'influence_score': self.influence_score,
                'content_quality': self.content_quality_score,
                'engagement': self.engagement_score,
                'reach': self.reach_score,
                'authenticity': self.authenticity_score,
                'consistency': self.consistency_score
            },
            'factors': {
                'follower_count': self.follower_count,
                'engagement_rate': self.engagement_rate,
                'posting_frequency': self.posting_frequency,
                'sentiment_score': self.sentiment_score
            },
            'changes': {
                'score_change': self.score_change,
                'rank_change': self.rank_change
            },
            'computed_at': self.computed_at.isoformat(),
            'computation_version': self.computation_version
        }

class CompetitorAnalysis(db.Model):
    """Competitor analysis data"""
    
    __tablename__ = 'competitor_analysis'
    
    id = db.Column(db.BigInteger, primary_key=True)
    influencer_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    competitor_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    
    # Similarity metrics
    content_similarity = db.Column(db.Float, default=0.0)  # 0-1
    audience_overlap = db.Column(db.Float, default=0.0)  # Estimated overlap
    hashtag_similarity = db.Column(db.Float, default=0.0)
    posting_time_similarity = db.Column(db.Float, default=0.0)
    
    # Performance comparison
    engagement_rate_diff = db.Column(db.Float, default=0.0)  # Difference in engagement
    follower_growth_diff = db.Column(db.Float, default=0.0)  # Growth rate difference
    influence_score_diff = db.Column(db.Float, default=0.0)
    
    # Shared elements
    common_hashtags = db.Column(JSON)  # Hashtags both use
    common_topics = db.Column(JSON)  # Topics both cover
    common_brands = db.Column(JSON)  # Brands both mention
    
    # Analysis metadata
    analysis_period_start = db.Column(db.DateTime, nullable=False)
    analysis_period_end = db.Column(db.DateTime, nullable=False)
    computed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('influencer_id', 'competitor_id', 'analysis_period_start', 
                          name='uq_competitor_analysis'),
        db.Index('idx_competitor_similarity', 'content_similarity'),
    )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'influencer_id': self.influencer_id,
            'competitor_id': self.competitor_id,
            'similarity': {
                'content': self.content_similarity,
                'audience_overlap': self.audience_overlap,
                'hashtags': self.hashtag_similarity,
                'posting_time': self.posting_time_similarity
            },
            'performance_diff': {
                'engagement_rate': self.engagement_rate_diff,
                'follower_growth': self.follower_growth_diff,
                'influence_score': self.influence_score_diff
            },
            'shared_elements': {
                'hashtags': self.common_hashtags,
                'topics': self.common_topics,
                'brands': self.common_brands
            },
            'analysis_period': {
                'start': self.analysis_period_start.isoformat(),
                'end': self.analysis_period_end.isoformat()
            },
            'computed_at': self.computed_at.isoformat()
        }