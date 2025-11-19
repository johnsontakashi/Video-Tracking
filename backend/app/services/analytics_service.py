import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from collections import Counter
import numpy as np
from textblob import TextBlob
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
import statistics

from app.models.influencer import Influencer, Post, Comment, InfluencerAnalytics
from app.models.analytics import (
    PostSentiment, CommentSentiment, SentimentLabel, 
    TrendingTopic, KeywordAnalysis, InfluenceScoreHistory, CompetitorAnalysis
)
from app import db

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

class AnalyticsService:
    """Service for processing influencer analytics and sentiment analysis"""
    
    def __init__(self):
        self.portuguese_stopwords = [
            'a', 'ao', 'aos', 'aquela', 'aquelas', 'aquele', 'aqueles', 'aquilo', 'as', 'até',
            'com', 'como', 'da', 'das', 'de', 'dela', 'delas', 'dele', 'deles', 'do', 'dos',
            'e', 'ela', 'elas', 'ele', 'eles', 'em', 'entre', 'era', 'eram', 'essa', 'essas',
            'esse', 'esses', 'esta', 'estão', 'estar', 'estas', 'estava', 'estavam', 'este',
            'estes', 'estou', 'está', 'eu', 'foi', 'for', 'foram', 'há', 'isso', 'isto', 'já',
            'mais', 'mas', 'me', 'muito', 'na', 'nas', 'nem', 'no', 'nos', 'nós', 'o', 'os',
            'ou', 'para', 'pela', 'pelas', 'pelo', 'pelos', 'por', 'que', 'se', 'sem', 'ser',
            'seu', 'seus', 'só', 'são', 'também', 'te', 'tem', 'ter', 'tu', 'tua', 'tuas',
            'um', 'uma', 'você', 'vocês', 'às'
        ]
        
        self.english_stopwords = [
            'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
            'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
            'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
            'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
            'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
            'while', 'of', 'at', 'by', 'for', 'with', 'through', 'during', 'before', 'after',
            'above', 'below', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
            'further', 'then', 'once'
        ]
        
        # Sentiment keywords for Portuguese and English
        self.positive_keywords = {
            'pt': ['amor', 'lindo', 'perfeito', 'incrível', 'maravilhoso', 'excelente', 'fantástico', 
                   'ótimo', 'bom', 'feliz', 'alegria', 'sucesso', 'top', 'demais', 'adorei'],
            'en': ['love', 'beautiful', 'perfect', 'amazing', 'wonderful', 'excellent', 'fantastic',
                   'great', 'good', 'happy', 'joy', 'success', 'awesome', 'best', 'incredible']
        }
        
        self.negative_keywords = {
            'pt': ['ódio', 'feio', 'ruim', 'terrível', 'péssimo', 'horrível', 'triste', 'raiva',
                   'fracasso', 'problema', 'chato', 'nojento', 'ridículo'],
            'en': ['hate', 'ugly', 'bad', 'terrible', 'awful', 'horrible', 'sad', 'angry',
                   'failure', 'problem', 'boring', 'disgusting', 'ridiculous']
        }
    
    async def analyze_post_sentiment(self, post: Post) -> PostSentiment:
        """Analyze sentiment for a single post"""
        try:
            if not post.content:
                return None
            
            # Detect language
            language = self._detect_language(post.content)
            
            # Perform sentiment analysis
            scores = await self._analyze_sentiment_scores(post.content, language)
            
            # Classify sentiment
            label, confidence = self._classify_sentiment(scores)
            
            # Extract keywords
            positive_keywords = self._extract_sentiment_keywords(post.content, language, 'positive')
            negative_keywords = self._extract_sentiment_keywords(post.content, language, 'negative')
            
            # Extract entities (basic implementation)
            entities = self._extract_entities(post.content)
            
            # Create sentiment record
            sentiment = PostSentiment(
                post_id=post.id,
                positive_score=scores['positive'],
                neutral_score=scores['neutral'], 
                negative_score=scores['negative'],
                compound_score=scores['compound'],
                label=label,
                confidence=confidence,
                language_detected=language,
                model_version='textblob_1.0',
                keywords_positive=positive_keywords,
                keywords_negative=negative_keywords,
                entities_mentioned=entities
            )
            
            # Check if sentiment already exists
            existing = PostSentiment.query.filter_by(post_id=post.id).first()
            if existing:
                # Update existing record
                existing.positive_score = sentiment.positive_score
                existing.neutral_score = sentiment.neutral_score
                existing.negative_score = sentiment.negative_score
                existing.compound_score = sentiment.compound_score
                existing.label = sentiment.label
                existing.confidence = sentiment.confidence
                existing.keywords_positive = sentiment.keywords_positive
                existing.keywords_negative = sentiment.keywords_negative
                existing.entities_mentioned = sentiment.entities_mentioned
                existing.analyzed_at = datetime.utcnow()
                sentiment = existing
            else:
                db.session.add(sentiment)
            
            db.session.commit()
            logger.info(f"Analyzed sentiment for post {post.id}: {label.value} ({confidence:.2f})")
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing post sentiment: {e}")
            db.session.rollback()
            return None
    
    async def analyze_comment_sentiment(self, comment: Comment) -> CommentSentiment:
        """Analyze sentiment for a single comment"""
        try:
            if not comment.content:
                return None
            
            # Detect language
            language = self._detect_language(comment.content)
            
            # Perform sentiment analysis
            scores = await self._analyze_sentiment_scores(comment.content, language)
            
            # Classify sentiment
            label, confidence = self._classify_sentiment(scores)
            
            # Basic spam detection
            is_spam = self._detect_spam(comment.content)
            
            # Create sentiment record
            sentiment = CommentSentiment(
                comment_id=comment.id,
                positive_score=scores['positive'],
                neutral_score=scores['neutral'],
                negative_score=scores['negative'],
                compound_score=scores['compound'],
                label=label,
                confidence=confidence,
                language_detected=language,
                is_spam=is_spam
            )
            
            # Check if sentiment already exists
            existing = CommentSentiment.query.filter_by(comment_id=comment.id).first()
            if existing:
                # Update existing record
                existing.positive_score = sentiment.positive_score
                existing.neutral_score = sentiment.neutral_score
                existing.negative_score = sentiment.negative_score
                existing.compound_score = sentiment.compound_score
                existing.label = sentiment.label
                existing.confidence = sentiment.confidence
                existing.is_spam = sentiment.is_spam
                existing.analyzed_at = datetime.utcnow()
                sentiment = existing
            else:
                db.session.add(sentiment)
            
            db.session.commit()
            
            return sentiment
            
        except Exception as e:
            logger.error(f"Error analyzing comment sentiment: {e}")
            db.session.rollback()
            return None
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        try:
            # Check for Portuguese indicators
            portuguese_indicators = ['é', 'ção', 'ão', 'muito', 'que', 'com', 'para', 'não']
            text_lower = text.lower()
            
            pt_count = sum(1 for word in portuguese_indicators if word in text_lower)
            
            # Simple heuristic
            if pt_count > 2:
                return 'pt'
            else:
                return 'en'
        except:
            return 'en'
    
    async def _analyze_sentiment_scores(self, text: str, language: str) -> Dict[str, float]:
        """Analyze sentiment scores using TextBlob"""
        try:
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Use TextBlob for sentiment analysis
            blob = TextBlob(cleaned_text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            # Convert to positive/neutral/negative scores
            if polarity > 0:
                positive = polarity
                negative = 0.0
                neutral = 1.0 - positive
            elif polarity < 0:
                positive = 0.0
                negative = abs(polarity)
                neutral = 1.0 - negative
            else:
                positive = 0.0
                negative = 0.0
                neutral = 1.0
            
            return {
                'positive': positive,
                'neutral': neutral,
                'negative': negative,
                'compound': polarity
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return {'positive': 0.0, 'neutral': 1.0, 'negative': 0.0, 'compound': 0.0}
    
    def _classify_sentiment(self, scores: Dict[str, float]) -> Tuple[SentimentLabel, float]:
        """Classify sentiment based on scores"""
        compound = scores['compound']
        
        if compound >= 0.05:
            label = SentimentLabel.POSITIVE
            confidence = scores['positive']
        elif compound <= -0.05:
            label = SentimentLabel.NEGATIVE
            confidence = scores['negative']
        else:
            label = SentimentLabel.NEUTRAL
            confidence = scores['neutral']
        
        # Check for mixed sentiment
        if scores['positive'] > 0.3 and scores['negative'] > 0.3:
            label = SentimentLabel.MIXED
            confidence = min(scores['positive'], scores['negative'])
        
        return label, min(max(confidence, 0.0), 1.0)
    
    def _extract_sentiment_keywords(self, text: str, language: str, sentiment_type: str) -> List[str]:
        """Extract sentiment-specific keywords"""
        try:
            text_lower = text.lower()
            keywords_dict = self.positive_keywords if sentiment_type == 'positive' else self.negative_keywords
            lang_keywords = keywords_dict.get(language, keywords_dict.get('en', []))
            
            found_keywords = []
            for keyword in lang_keywords:
                if keyword in text_lower:
                    found_keywords.append(keyword)
            
            return found_keywords
            
        except Exception as e:
            logger.error(f"Error extracting sentiment keywords: {e}")
            return []
    
    def _extract_entities(self, text: str) -> List[str]:
        """Basic entity extraction (brands, mentions)"""
        try:
            entities = []
            
            # Extract mentions
            mentions = re.findall(r'@(\w+)', text)
            entities.extend([f"@{mention}" for mention in mentions])
            
            # Extract hashtags
            hashtags = re.findall(r'#(\w+)', text)
            entities.extend([f"#{hashtag}" for hashtag in hashtags])
            
            # Extract basic brand names (simple pattern matching)
            brand_patterns = [
                r'\b(Nike|Adidas|Apple|Samsung|Instagram|YouTube|TikTok|Twitter)\b'
            ]
            
            for pattern in brand_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                entities.extend(matches)
            
            return list(set(entities))
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return []
    
    def _detect_spam(self, text: str) -> bool:
        """Basic spam detection"""
        try:
            text_lower = text.lower()
            
            # Spam indicators
            spam_patterns = [
                r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+',  # URLs
                r'\b(buy now|click here|free money|win cash|urgent)\b',  # Spam phrases
                r'(.)\1{5,}',  # Repeated characters
            ]
            
            for pattern in spam_patterns:
                if re.search(pattern, text_lower):
                    return True
            
            # Check for excessive capitalization
            if len([c for c in text if c.isupper()]) / len(text) > 0.7:
                return True
            
            return False
            
        except Exception:
            return False
    
    def _clean_text(self, text: str) -> str:
        """Clean text for analysis"""
        try:
            # Remove URLs
            text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove excessive punctuation
            text = re.sub(r'[!]{2,}', '!', text)
            text = re.sub(r'[?]{2,}', '?', text)
            
            return text.strip()
            
        except Exception:
            return text
    
    async def calculate_influencer_analytics(self, influencer: Influencer, 
                                           days_back: int = 30) -> InfluencerAnalytics:
        """Calculate comprehensive analytics for an influencer"""
        try:
            logger.info(f"Calculating analytics for influencer {influencer.username}")
            
            # Define analysis period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days_back)
            
            # Get posts in the period
            posts = Post.query.filter(
                Post.influencer_id == influencer.id,
                Post.posted_at >= start_date,
                Post.posted_at <= end_date
            ).all()
            
            if not posts:
                logger.warning(f"No posts found for influencer {influencer.username} in the last {days_back} days")
                return None
            
            # Calculate engagement metrics
            engagement_stats = await self._calculate_engagement_metrics(posts, influencer)
            
            # Calculate sentiment metrics
            sentiment_stats = await self._calculate_sentiment_metrics(posts)
            
            # Calculate content metrics
            content_stats = await self._calculate_content_metrics(posts)
            
            # Calculate influence score
            influence_score = await self._calculate_influence_score(influencer, posts, engagement_stats)
            
            # Extract top keywords and hashtags
            keywords_data = await self._extract_keywords_and_topics(posts)
            
            # Create or update analytics record
            analytics = InfluencerAnalytics(
                influencer_id=influencer.id,
                influence_score=influence_score,
                engagement_rate=engagement_stats['engagement_rate'],
                consistency_score=engagement_stats['consistency_score'],
                growth_rate=engagement_stats['growth_rate'],
                sentiment_positive=sentiment_stats['positive'],
                sentiment_neutral=sentiment_stats['neutral'],
                sentiment_negative=sentiment_stats['negative'],
                sentiment_compound=sentiment_stats['compound'],
                avg_likes=content_stats['avg_likes'],
                avg_comments=content_stats['avg_comments'],
                avg_shares=content_stats['avg_shares'],
                top_hashtags=keywords_data['hashtags'],
                top_keywords=keywords_data['keywords'],
                period_start=start_date,
                period_end=end_date,
                posts_analyzed=len(posts)
            )
            
            # Check if analytics already exists for this period
            existing = InfluencerAnalytics.query.filter(
                InfluencerAnalytics.influencer_id == influencer.id,
                InfluencerAnalytics.period_start == start_date,
                InfluencerAnalytics.period_end == end_date
            ).first()
            
            if existing:
                # Update existing record
                existing.influence_score = analytics.influence_score
                existing.engagement_rate = analytics.engagement_rate
                existing.consistency_score = analytics.consistency_score
                existing.growth_rate = analytics.growth_rate
                existing.sentiment_positive = analytics.sentiment_positive
                existing.sentiment_neutral = analytics.sentiment_neutral
                existing.sentiment_negative = analytics.sentiment_negative
                existing.sentiment_compound = analytics.sentiment_compound
                existing.avg_likes = analytics.avg_likes
                existing.avg_comments = analytics.avg_comments
                existing.avg_shares = analytics.avg_shares
                existing.top_hashtags = analytics.top_hashtags
                existing.top_keywords = analytics.top_keywords
                existing.posts_analyzed = analytics.posts_analyzed
                existing.computed_at = datetime.utcnow()
                analytics = existing
            else:
                db.session.add(analytics)
            
            db.session.commit()
            
            # Record influence score history
            await self._record_influence_score_history(influencer, analytics)
            
            logger.info(f"Analytics calculated for {influencer.username}: Influence Score {influence_score:.2f}")
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error calculating influencer analytics: {e}")
            db.session.rollback()
            return None
    
    async def _calculate_engagement_metrics(self, posts: List[Post], influencer: Influencer) -> Dict[str, float]:
        """Calculate engagement-related metrics"""
        try:
            if not posts or not influencer.follower_count:
                return {
                    'engagement_rate': 0.0,
                    'consistency_score': 0.0,
                    'growth_rate': 0.0
                }
            
            # Calculate engagement rate
            total_engagement = sum(
                (post.likes_count or 0) + (post.comments_count or 0) + (post.shares_count or 0)
                for post in posts
            )
            avg_engagement = total_engagement / len(posts)
            engagement_rate = (avg_engagement / influencer.follower_count) * 100
            
            # Calculate posting consistency (coefficient of variation)
            post_intervals = []
            sorted_posts = sorted(posts, key=lambda p: p.posted_at)
            
            for i in range(1, len(sorted_posts)):
                interval = (sorted_posts[i].posted_at - sorted_posts[i-1].posted_at).total_seconds() / 3600
                post_intervals.append(interval)
            
            if post_intervals:
                mean_interval = statistics.mean(post_intervals)
                std_interval = statistics.stdev(post_intervals) if len(post_intervals) > 1 else 0
                consistency_score = max(0, 1 - (std_interval / mean_interval if mean_interval > 0 else 1))
            else:
                consistency_score = 0.0
            
            # Calculate growth rate (simplified - would need historical data)
            growth_rate = 0.0  # Placeholder - implement with historical follower data
            
            return {
                'engagement_rate': min(engagement_rate, 100.0),
                'consistency_score': min(consistency_score, 1.0),
                'growth_rate': growth_rate
            }
            
        except Exception as e:
            logger.error(f"Error calculating engagement metrics: {e}")
            return {'engagement_rate': 0.0, 'consistency_score': 0.0, 'growth_rate': 0.0}
    
    async def _calculate_sentiment_metrics(self, posts: List[Post]) -> Dict[str, float]:
        """Calculate sentiment metrics for posts"""
        try:
            sentiments = []
            
            for post in posts:
                sentiment = PostSentiment.query.filter_by(post_id=post.id).first()
                if sentiment:
                    sentiments.append(sentiment)
                else:
                    # Analyze sentiment if not exists
                    sentiment = await self.analyze_post_sentiment(post)
                    if sentiment:
                        sentiments.append(sentiment)
            
            if not sentiments:
                return {'positive': 0.0, 'neutral': 1.0, 'negative': 0.0, 'compound': 0.0}
            
            # Calculate average sentiment scores
            avg_positive = statistics.mean([s.positive_score for s in sentiments])
            avg_neutral = statistics.mean([s.neutral_score for s in sentiments])
            avg_negative = statistics.mean([s.negative_score for s in sentiments])
            avg_compound = statistics.mean([s.compound_score for s in sentiments])
            
            return {
                'positive': avg_positive,
                'neutral': avg_neutral,
                'negative': avg_negative,
                'compound': avg_compound
            }
            
        except Exception as e:
            logger.error(f"Error calculating sentiment metrics: {e}")
            return {'positive': 0.0, 'neutral': 1.0, 'negative': 0.0, 'compound': 0.0}
    
    async def _calculate_content_metrics(self, posts: List[Post]) -> Dict[str, float]:
        """Calculate content-related metrics"""
        try:
            if not posts:
                return {'avg_likes': 0.0, 'avg_comments': 0.0, 'avg_shares': 0.0}
            
            avg_likes = statistics.mean([post.likes_count or 0 for post in posts])
            avg_comments = statistics.mean([post.comments_count or 0 for post in posts])
            avg_shares = statistics.mean([post.shares_count or 0 for post in posts])
            
            return {
                'avg_likes': avg_likes,
                'avg_comments': avg_comments,
                'avg_shares': avg_shares
            }
            
        except Exception as e:
            logger.error(f"Error calculating content metrics: {e}")
            return {'avg_likes': 0.0, 'avg_comments': 0.0, 'avg_shares': 0.0}
    
    async def _calculate_influence_score(self, influencer: Influencer, posts: List[Post], 
                                       engagement_stats: Dict[str, float]) -> float:
        """Calculate comprehensive influence score (0-100)"""
        try:
            # Base score components (weighted)
            components = {
                'follower_score': 0.0,      # 25%
                'engagement_score': 0.0,    # 30%
                'content_quality': 0.0,     # 20%
                'consistency': 0.0,         # 15%
                'growth': 0.0              # 10%
            }
            
            # 1. Follower Score (logarithmic scale)
            if influencer.follower_count > 0:
                # Normalize follower count (log scale)
                follower_log = np.log10(max(influencer.follower_count, 1))
                components['follower_score'] = min(follower_log / 8.0, 1.0) * 100  # Max at 100M followers
            
            # 2. Engagement Score
            engagement_rate = engagement_stats['engagement_rate']
            components['engagement_score'] = min(engagement_rate * 10, 100)  # 10% engagement = 100 points
            
            # 3. Content Quality Score (based on sentiment and performance)
            if posts:
                # Get average engagement per post
                avg_engagement = statistics.mean([
                    ((post.likes_count or 0) + (post.comments_count or 0) + (post.shares_count or 0))
                    for post in posts
                ])
                
                # Normalize based on follower count
                if influencer.follower_count > 0:
                    quality_ratio = avg_engagement / influencer.follower_count
                    components['content_quality'] = min(quality_ratio * 1000, 100)
            
            # 4. Consistency Score
            components['consistency'] = engagement_stats['consistency_score'] * 100
            
            # 5. Growth Score (placeholder)
            components['growth'] = engagement_stats['growth_rate'] * 100
            
            # Calculate weighted influence score
            weights = {
                'follower_score': 0.25,
                'engagement_score': 0.30,
                'content_quality': 0.20,
                'consistency': 0.15,
                'growth': 0.10
            }
            
            influence_score = sum(
                components[component] * weights[component]
                for component in components
            )
            
            # Apply platform-specific adjustments
            platform_multipliers = {
                'instagram': 1.0,
                'youtube': 1.1,  # Higher weight for YouTube
                'tiktok': 0.9,   # Slightly lower for TikTok
                'twitter': 0.8   # Lower for Twitter
            }
            
            multiplier = platform_multipliers.get(influencer.platform.value, 1.0)
            influence_score *= multiplier
            
            return min(max(influence_score, 0.0), 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating influence score: {e}")
            return 0.0
    
    async def _extract_keywords_and_topics(self, posts: List[Post]) -> Dict[str, List]:
        """Extract keywords and topics from posts"""
        try:
            if not posts:
                return {'keywords': [], 'hashtags': []}
            
            # Combine all post content
            all_text = ' '.join([post.content or '' for post in posts])
            all_hashtags = []
            
            for post in posts:
                if post.hashtags:
                    all_hashtags.extend(post.hashtags)
            
            # Extract keywords using simple frequency analysis
            words = re.findall(r'\b\w+\b', all_text.lower())
            
            # Filter out stopwords
            stopwords = set(self.portuguese_stopwords + self.english_stopwords)
            filtered_words = [word for word in words if word not in stopwords and len(word) > 2]
            
            # Count word frequency
            word_freq = Counter(filtered_words)
            top_keywords = [
                {'keyword': word, 'frequency': count}
                for word, count in word_freq.most_common(20)
            ]
            
            # Count hashtag frequency
            hashtag_freq = Counter(all_hashtags)
            top_hashtags = [
                {'hashtag': hashtag, 'frequency': count}
                for hashtag, count in hashtag_freq.most_common(10)
            ]
            
            return {
                'keywords': top_keywords,
                'hashtags': top_hashtags
            }
            
        except Exception as e:
            logger.error(f"Error extracting keywords and topics: {e}")
            return {'keywords': [], 'hashtags': []}
    
    async def _record_influence_score_history(self, influencer: Influencer, 
                                            analytics: InfluencerAnalytics):
        """Record influence score history for tracking changes"""
        try:
            # Get previous score
            previous_score = InfluenceScoreHistory.query.filter_by(
                influencer_id=influencer.id
            ).order_by(InfluenceScoreHistory.computed_at.desc()).first()
            
            score_change = 0.0
            if previous_score:
                score_change = analytics.influence_score - previous_score.influence_score
            
            # Create history record
            history = InfluenceScoreHistory(
                influencer_id=influencer.id,
                influence_score=analytics.influence_score,
                content_quality_score=50.0,  # Placeholder
                engagement_score=analytics.engagement_rate,
                reach_score=0.0,  # Placeholder
                authenticity_score=0.0,  # Placeholder
                consistency_score=analytics.consistency_score,
                follower_count=influencer.follower_count,
                engagement_rate=analytics.engagement_rate,
                posting_frequency=analytics.posts_analyzed / 30.0,  # Posts per day
                sentiment_score=analytics.sentiment_compound,
                score_change=score_change,
                computation_version='v1.0'
            )
            
            db.session.add(history)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording influence score history: {e}")
            db.session.rollback()
    
    async def detect_trending_topics(self, hours_back: int = 24) -> List[TrendingTopic]:
        """Detect trending topics across all posts"""
        try:
            # Get recent posts
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            recent_posts = Post.query.filter(
                Post.posted_at >= cutoff_time
            ).all()
            
            if not recent_posts:
                return []
            
            # Extract and count hashtags
            all_hashtags = []
            for post in recent_posts:
                if post.hashtags:
                    all_hashtags.extend(post.hashtags)
            
            hashtag_counts = Counter(all_hashtags)
            
            # Identify trending hashtags (simple threshold-based approach)
            trending_topics = []
            for hashtag, count in hashtag_counts.most_common(50):
                if count >= 5:  # Minimum mentions threshold
                    # Calculate growth rate (simplified)
                    velocity = count / hours_back
                    
                    # Check if topic already exists
                    existing_topic = TrendingTopic.query.filter_by(
                        hashtag=hashtag
                    ).first()
                    
                    if existing_topic:
                        # Update existing topic
                        existing_topic.mention_count = count
                        existing_topic.velocity = velocity
                        existing_topic.last_updated = datetime.utcnow()
                        trending_topics.append(existing_topic)
                    else:
                        # Create new trending topic
                        topic = TrendingTopic(
                            topic=hashtag,
                            hashtag=hashtag,
                            mention_count=count,
                            velocity=velocity,
                            trending_since=cutoff_time,
                            category='general'  # Would implement categorization
                        )
                        db.session.add(topic)
                        trending_topics.append(topic)
            
            db.session.commit()
            logger.info(f"Detected {len(trending_topics)} trending topics")
            
            return trending_topics
            
        except Exception as e:
            logger.error(f"Error detecting trending topics: {e}")
            db.session.rollback()
            return []
    
    async def process_bulk_sentiment_analysis(self, batch_size: int = 100) -> int:
        """Process sentiment analysis for posts that haven't been analyzed"""
        try:
            # Get posts without sentiment analysis
            posts_without_sentiment = db.session.query(Post).outerjoin(
                PostSentiment, Post.id == PostSentiment.post_id
            ).filter(
                PostSentiment.id == None
            ).limit(batch_size).all()
            
            if not posts_without_sentiment:
                logger.info("No posts need sentiment analysis")
                return 0
            
            analyzed_count = 0
            
            for post in posts_without_sentiment:
                try:
                    sentiment = await self.analyze_post_sentiment(post)
                    if sentiment:
                        analyzed_count += 1
                        
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error analyzing sentiment for post {post.id}: {e}")
                    continue
            
            logger.info(f"Processed sentiment analysis for {analyzed_count} posts")
            return analyzed_count
            
        except Exception as e:
            logger.error(f"Error in bulk sentiment analysis: {e}")
            return 0
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get summary statistics for analytics"""
        try:
            summary = {
                'total_posts_analyzed': PostSentiment.query.count(),
                'total_comments_analyzed': CommentSentiment.query.count(),
                'trending_topics_count': TrendingTopic.query.filter_by(is_active=True).count(),
                'influencers_with_analytics': InfluencerAnalytics.query.count(),
                'sentiment_distribution': {
                    'positive': PostSentiment.query.filter_by(label=SentimentLabel.POSITIVE).count(),
                    'neutral': PostSentiment.query.filter_by(label=SentimentLabel.NEUTRAL).count(),
                    'negative': PostSentiment.query.filter_by(label=SentimentLabel.NEGATIVE).count(),
                    'mixed': PostSentiment.query.filter_by(label=SentimentLabel.MIXED).count()
                },
                'avg_influence_score': db.session.query(db.func.avg(InfluencerAnalytics.influence_score)).scalar() or 0
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {}