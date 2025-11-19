import asyncio
import aiohttp
import json
import re
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import logging

from app.collectors.base_collector import BaseCollector, CollectionResult, CollectionError, AuthenticationError
from app.models.influencer import Platform, Influencer, Post, Comment
from app.models.collection import CollectionTask
from app import db

logger = logging.getLogger(__name__)

class InstagramCollector(BaseCollector):
    """Instagram data collector with API and web scraping capabilities"""
    
    def __init__(self):
        super().__init__(Platform.INSTAGRAM)
        self.api_base = "https://graph.instagram.com"
        self.web_base = "https://www.instagram.com"
        self.access_token = None
        self.session_cookies = {}
        
        # Instagram-specific rate limits
        self.api_limits = {
            'user_media': 200,      # per hour
            'media_insights': 100,   # per hour
            'user_info': 500        # per hour
        }
        
        # Common Instagram headers
        self.instagram_headers = {
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': '',
            'X-Instagram-AJAX': '1',
            'Referer': 'https://www.instagram.com/',
            'Origin': 'https://www.instagram.com',
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Instagram Basic Display API"""
        try:
            # For production, this would use stored access tokens
            # For now, we'll implement web-based authentication
            return await self._authenticate_web()
        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
            return False
    
    async def _authenticate_web(self) -> bool:
        """Web-based authentication for Instagram"""
        try:
            # Get initial page to establish session
            success, data, error = await self.make_request(
                'session_init',
                f"{self.web_base}/",
                headers=self.instagram_headers
            )
            
            if success and data:
                # Extract CSRF token from response
                csrf_token = self._extract_csrf_token(data.get('raw_response', ''))
                if csrf_token:
                    self.instagram_headers['X-CSRFToken'] = csrf_token
                    logger.info("Instagram web session initialized successfully")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Instagram web authentication error: {e}")
            return False
    
    def _extract_csrf_token(self, html_content: str) -> Optional[str]:
        """Extract CSRF token from HTML response"""
        try:
            # Look for csrf_token in various formats
            patterns = [
                r'"csrf_token":"([^"]+)"',
                r'csrftoken=([^;]+)',
                r'"token":"([^"]+)"'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html_content)
                if match:
                    return match.group(1)
            
            return None
        except Exception:
            return None
    
    async def collect_influencer_data(self, username: str) -> Dict:
        """Collect Instagram influencer profile data"""
        try:
            logger.info(f"Collecting Instagram profile data for {username}")
            
            # Try API first, fallback to web scraping
            profile_data = await self._get_profile_via_api(username)
            if not profile_data:
                profile_data = await self._get_profile_via_web(username)
            
            if profile_data:
                return self.normalize_influencer_data(profile_data)
            
            raise CollectionError(f"Failed to collect profile data for {username}")
            
        except Exception as e:
            logger.error(f"Error collecting Instagram profile {username}: {e}")
            raise CollectionError(f"Profile collection failed: {str(e)}")
    
    async def _get_profile_via_api(self, username: str) -> Optional[Dict]:
        """Get profile data via Instagram Basic Display API"""
        try:
            if not self.access_token:
                return None
            
            # Instagram Basic Display API endpoint
            url = f"{self.api_base}/me"
            params = {
                'fields': 'id,username,account_type,media_count',
                'access_token': self.access_token
            }
            
            success, data, error = await self.make_request(
                'user_info',
                url,
                params=params
            )
            
            if success and data:
                return data
                
        except Exception as e:
            logger.warning(f"API profile collection failed for {username}: {e}")
        
        return None
    
    async def _get_profile_via_web(self, username: str) -> Optional[Dict]:
        """Get profile data via web scraping"""
        try:
            url = f"{self.web_base}/{username}/"
            
            success, data, error = await self.make_request(
                'profile_scrape',
                url,
                headers=self.instagram_headers
            )
            
            if success and data:
                html_content = data.get('raw_response', '')
                return self._parse_profile_from_html(html_content, username)
                
        except Exception as e:
            logger.error(f"Web scraping failed for {username}: {e}")
        
        return None
    
    def _parse_profile_from_html(self, html: str, username: str) -> Dict:
        """Parse profile data from Instagram HTML"""
        try:
            profile_data = {
                'username': username,
                'id': username,  # Will be updated if found
                'display_name': username,
                'bio': '',
                'follower_count': 0,
                'following_count': 0,
                'post_count': 0,
                'verified': False,
                'business_account': False,
                'profile_image_url': '',
                'external_url': ''
            }
            
            # Extract JSON data from script tags
            json_pattern = r'<script type="application/ld\+json">({.*?})</script>'
            json_matches = re.findall(json_pattern, html, re.DOTALL)
            
            for json_str in json_matches:
                try:
                    data = json.loads(json_str)
                    if '@type' in data and data['@type'] == 'Person':
                        profile_data.update({
                            'display_name': data.get('name', username),
                            'bio': data.get('description', ''),
                            'profile_image_url': data.get('image', '')
                        })
                        break
                except json.JSONDecodeError:
                    continue
            
            # Extract metrics from HTML patterns
            followers_match = re.search(r'"edge_followed_by":{"count":(\d+)}', html)
            if followers_match:
                profile_data['follower_count'] = int(followers_match.group(1))
            
            following_match = re.search(r'"edge_follow":{"count":(\d+)}', html)
            if following_match:
                profile_data['following_count'] = int(following_match.group(1))
            
            posts_match = re.search(r'"edge_owner_to_timeline_media":{"count":(\d+)}', html)
            if posts_match:
                profile_data['post_count'] = int(posts_match.group(1))
            
            # Check for verification
            if 'is_verified":true' in html:
                profile_data['verified'] = True
            
            # Check for business account
            if 'is_business_account":true' in html:
                profile_data['business_account'] = True
            
            return profile_data
            
        except Exception as e:
            logger.error(f"Error parsing profile HTML: {e}")
            raise CollectionError("Failed to parse profile data")
    
    async def collect_posts(self, influencer_id: str, limit: int = 50) -> List[Dict]:
        """Collect Instagram posts for an influencer"""
        try:
            logger.info(f"Collecting Instagram posts for influencer {influencer_id}")
            
            posts = []
            cursor = None
            collected = 0
            
            while collected < limit:
                batch_posts, next_cursor = await self._collect_posts_batch(
                    influencer_id, cursor, min(25, limit - collected)
                )
                
                if not batch_posts:
                    break
                
                posts.extend(batch_posts)
                collected += len(batch_posts)
                cursor = next_cursor
                
                if not cursor:
                    break
                
                # Rate limiting between batches
                await asyncio.sleep(2)
            
            return [self.normalize_post_data(post) for post in posts[:limit]]
            
        except Exception as e:
            logger.error(f"Error collecting Instagram posts: {e}")
            raise CollectionError(f"Post collection failed: {str(e)}")
    
    async def _collect_posts_batch(self, influencer_id: str, cursor: str = None, 
                                 count: int = 25) -> Tuple[List[Dict], Optional[str]]:
        """Collect a batch of posts"""
        try:
            # Try API first
            if self.access_token:
                return await self._collect_posts_api(influencer_id, cursor, count)
            
            # Fallback to web scraping
            return await self._collect_posts_web(influencer_id, cursor, count)
            
        except Exception as e:
            logger.error(f"Error in posts batch collection: {e}")
            return [], None
    
    async def _collect_posts_api(self, influencer_id: str, cursor: str = None, 
                               count: int = 25) -> Tuple[List[Dict], Optional[str]]:
        """Collect posts via API"""
        try:
            url = f"{self.api_base}/{influencer_id}/media"
            params = {
                'fields': 'id,media_type,media_url,thumbnail_url,permalink,caption,timestamp,like_count,comments_count',
                'limit': count,
                'access_token': self.access_token
            }
            
            if cursor:
                params['after'] = cursor
            
            success, data, error = await self.make_request(
                'user_media',
                url,
                params=params
            )
            
            if success and data:
                posts = data.get('data', [])
                next_cursor = data.get('paging', {}).get('cursors', {}).get('after')
                return posts, next_cursor
                
        except Exception as e:
            logger.warning(f"API post collection failed: {e}")
        
        return [], None
    
    async def _collect_posts_web(self, username: str, cursor: str = None, 
                               count: int = 25) -> Tuple[List[Dict], Optional[str]]:
        """Collect posts via web scraping"""
        try:
            if cursor:
                # Use GraphQL endpoint for pagination
                url = f"{self.web_base}/graphql/query/"
                params = {
                    'query_hash': 'e769aa130647d2354c40ea6a439bfc08',  # Posts query hash
                    'variables': json.dumps({
                        'id': username,
                        'first': count,
                        'after': cursor
                    })
                }
            else:
                # Initial page load
                url = f"{self.web_base}/{username}/"
                params = None
            
            success, data, error = await self.make_request(
                'posts_scrape',
                url,
                params=params,
                headers=self.instagram_headers
            )
            
            if success and data:
                return self._parse_posts_from_response(data, username)
                
        except Exception as e:
            logger.error(f"Web scraping posts failed: {e}")
        
        return [], None
    
    def _parse_posts_from_response(self, data: Dict, username: str) -> Tuple[List[Dict], Optional[str]]:
        """Parse posts from web response"""
        posts = []
        next_cursor = None
        
        try:
            html_content = data.get('raw_response', '')
            
            # Look for JSON data containing posts
            json_patterns = [
                r'window\._sharedData = ({.*?});',
                r'"edge_owner_to_timeline_media":{.*?"edges":(\[.*?\])',
                r'"data":{.*?"user":{.*?"edge_owner_to_timeline_media":{.*?"edges":(\[.*?\])'
            ]
            
            for pattern in json_patterns:
                matches = re.findall(pattern, html_content, re.DOTALL)
                for match in matches:
                    try:
                        if match.startswith('['):
                            # Direct edges array
                            edges_data = json.loads(match)
                        else:
                            # Full shared data
                            shared_data = json.loads(match)
                            edges_data = self._extract_posts_from_shared_data(shared_data)
                        
                        for edge in edges_data:
                            node = edge.get('node', {})
                            if node:
                                post_data = self._parse_post_node(node, username)
                                if post_data:
                                    posts.append(post_data)
                        
                        # Look for pagination cursor
                        if len(edges_data) > 0:
                            last_edge = edges_data[-1]
                            next_cursor = last_edge.get('cursor')
                        
                        break
                        
                    except (json.JSONDecodeError, KeyError):
                        continue
            
        except Exception as e:
            logger.error(f"Error parsing posts from response: {e}")
        
        return posts, next_cursor
    
    def _extract_posts_from_shared_data(self, shared_data: Dict) -> List[Dict]:
        """Extract posts from Instagram's shared data structure"""
        try:
            # Navigate through the nested structure to find posts
            entry_data = shared_data.get('entry_data', {})
            profile_page = entry_data.get('ProfilePage', [])
            
            if profile_page:
                user_data = profile_page[0].get('user', {})
                timeline_media = user_data.get('edge_owner_to_timeline_media', {})
                return timeline_media.get('edges', [])
                
        except Exception:
            pass
        
        return []
    
    def _parse_post_node(self, node: Dict, username: str) -> Optional[Dict]:
        """Parse a single post node from Instagram data"""
        try:
            return {
                'id': node.get('id'),
                'shortcode': node.get('shortcode'),
                'media_type': node.get('__typename', 'GraphImage'),
                'caption': self._extract_caption(node),
                'media_url': node.get('display_url'),
                'thumbnail_url': node.get('thumbnail_src'),
                'permalink': f"https://www.instagram.com/p/{node.get('shortcode')}/",
                'timestamp': node.get('taken_at_timestamp'),
                'like_count': node.get('edge_liked_by', {}).get('count', 0),
                'comments_count': node.get('edge_media_to_comment', {}).get('count', 0),
                'hashtags': self._extract_hashtags(node),
                'mentions': self._extract_mentions(node),
                'location': node.get('location'),
                'username': username
            }
        except Exception as e:
            logger.error(f"Error parsing post node: {e}")
            return None
    
    def _extract_caption(self, node: Dict) -> str:
        """Extract caption text from post node"""
        try:
            caption_edges = node.get('edge_media_to_caption', {}).get('edges', [])
            if caption_edges:
                return caption_edges[0].get('node', {}).get('text', '')
        except Exception:
            pass
        return ''
    
    def _extract_hashtags(self, node: Dict) -> List[str]:
        """Extract hashtags from post caption"""
        caption = self._extract_caption(node)
        hashtag_pattern = r'#(\w+)'
        return re.findall(hashtag_pattern, caption.lower())
    
    def _extract_mentions(self, node: Dict) -> List[str]:
        """Extract mentions from post caption"""
        caption = self._extract_caption(node)
        mention_pattern = r'@(\w+)'
        return re.findall(mention_pattern, caption.lower())
    
    async def collect_comments(self, post_id: str, limit: int = 100) -> List[Dict]:
        """Collect comments for an Instagram post"""
        try:
            logger.info(f"Collecting Instagram comments for post {post_id}")
            
            comments = []
            cursor = None
            collected = 0
            
            while collected < limit:
                batch_comments, next_cursor = await self._collect_comments_batch(
                    post_id, cursor, min(50, limit - collected)
                )
                
                if not batch_comments:
                    break
                
                comments.extend(batch_comments)
                collected += len(batch_comments)
                cursor = next_cursor
                
                if not cursor:
                    break
                
                # Rate limiting between batches
                await asyncio.sleep(1)
            
            return [self.normalize_comment_data(comment) for comment in comments[:limit]]
            
        except Exception as e:
            logger.error(f"Error collecting Instagram comments: {e}")
            raise CollectionError(f"Comment collection failed: {str(e)}")
    
    async def _collect_comments_batch(self, post_id: str, cursor: str = None, 
                                    count: int = 50) -> Tuple[List[Dict], Optional[str]]:
        """Collect a batch of comments"""
        try:
            # Use Instagram's GraphQL endpoint for comments
            url = f"{self.web_base}/graphql/query/"
            
            variables = {
                'shortcode': post_id,
                'first': count
            }
            
            if cursor:
                variables['after'] = cursor
            
            params = {
                'query_hash': 'bc3296d1ce80a24b1b6e40b1e72903f5',  # Comments query hash
                'variables': json.dumps(variables)
            }
            
            success, data, error = await self.make_request(
                'comments_scrape',
                url,
                params=params,
                headers=self.instagram_headers
            )
            
            if success and data:
                return self._parse_comments_from_response(data)
                
        except Exception as e:
            logger.error(f"Error collecting comments batch: {e}")
        
        return [], None
    
    def _parse_comments_from_response(self, data: Dict) -> Tuple[List[Dict], Optional[str]]:
        """Parse comments from GraphQL response"""
        comments = []
        next_cursor = None
        
        try:
            if isinstance(data, dict) and 'data' in data:
                # GraphQL response
                media = data['data'].get('shortcode_media', {})
                comment_data = media.get('edge_media_to_parent_comment', {})
                edges = comment_data.get('edges', [])
                
                for edge in edges:
                    node = edge.get('node', {})
                    comment = self._parse_comment_node(node)
                    if comment:
                        comments.append(comment)
                
                # Get pagination cursor
                page_info = comment_data.get('page_info', {})
                if page_info.get('has_next_page'):
                    next_cursor = page_info.get('end_cursor')
            
        except Exception as e:
            logger.error(f"Error parsing comments response: {e}")
        
        return comments, next_cursor
    
    def _parse_comment_node(self, node: Dict) -> Optional[Dict]:
        """Parse a single comment node"""
        try:
            owner = node.get('owner', {})
            return {
                'id': node.get('id'),
                'text': node.get('text', ''),
                'author_username': owner.get('username'),
                'author_profile_pic': owner.get('profile_pic_url'),
                'timestamp': node.get('created_at'),
                'like_count': node.get('edge_liked_by', {}).get('count', 0),
                'reply_count': node.get('edge_threaded_comments', {}).get('count', 0)
            }
        except Exception as e:
            logger.error(f"Error parsing comment node: {e}")
            return None
    
    def normalize_influencer_data(self, raw_data: Dict) -> Dict:
        """Normalize raw Instagram influencer data to standard format"""
        try:
            return {
                'external_id': str(raw_data.get('id', raw_data.get('username'))),
                'username': raw_data.get('username', ''),
                'display_name': raw_data.get('display_name', raw_data.get('name', '')),
                'platform': Platform.INSTAGRAM,
                'bio': raw_data.get('bio', ''),
                'profile_image_url': raw_data.get('profile_image_url', raw_data.get('profile_pic_url', '')),
                'profile_url': f"https://www.instagram.com/{raw_data.get('username', '')}/",
                'verified': raw_data.get('verified', False),
                'business_account': raw_data.get('business_account', False),
                'follower_count': raw_data.get('follower_count', 0),
                'following_count': raw_data.get('following_count', 0),
                'post_count': raw_data.get('post_count', raw_data.get('media_count', 0)),
                'location': raw_data.get('location'),
                'external_url': raw_data.get('external_url'),
                'raw_data': raw_data
            }
        except Exception as e:
            logger.error(f"Error normalizing influencer data: {e}")
            raise CollectionError("Failed to normalize influencer data")
    
    def normalize_post_data(self, raw_data: Dict) -> Dict:
        """Normalize raw Instagram post data to standard format"""
        try:
            posted_at = raw_data.get('timestamp')
            if isinstance(posted_at, (int, float)):
                posted_at = datetime.fromtimestamp(posted_at)
            elif isinstance(posted_at, str):
                posted_at = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            else:
                posted_at = datetime.utcnow()
            
            return {
                'external_id': raw_data.get('id', raw_data.get('shortcode')),
                'platform': Platform.INSTAGRAM,
                'content': raw_data.get('caption', ''),
                'content_type': self._map_content_type(raw_data.get('media_type', 'GraphImage')),
                'media_urls': [raw_data.get('media_url')] if raw_data.get('media_url') else [],
                'hashtags': raw_data.get('hashtags', []),
                'mentions': raw_data.get('mentions', []),
                'likes_count': raw_data.get('like_count', 0),
                'comments_count': raw_data.get('comments_count', 0),
                'shares_count': 0,  # Instagram doesn't provide shares
                'views_count': raw_data.get('views_count', 0),
                'posted_at': posted_at,
                'location_data': raw_data.get('location'),
                'raw_data': raw_data
            }
        except Exception as e:
            logger.error(f"Error normalizing post data: {e}")
            raise CollectionError("Failed to normalize post data")
    
    def normalize_comment_data(self, raw_data: Dict) -> Dict:
        """Normalize raw Instagram comment data to standard format"""
        try:
            posted_at = raw_data.get('timestamp')
            if isinstance(posted_at, (int, float)):
                posted_at = datetime.fromtimestamp(posted_at)
            elif isinstance(posted_at, str):
                posted_at = datetime.fromisoformat(posted_at.replace('Z', '+00:00'))
            else:
                posted_at = datetime.utcnow()
            
            return {
                'external_id': raw_data.get('id'),
                'content': raw_data.get('text', ''),
                'author_username': raw_data.get('author_username', ''),
                'author_display_name': raw_data.get('author_display_name', ''),
                'likes_count': raw_data.get('like_count', 0),
                'replies_count': raw_data.get('reply_count', 0),
                'posted_at': posted_at,
                'raw_data': raw_data
            }
        except Exception as e:
            logger.error(f"Error normalizing comment data: {e}")
            raise CollectionError("Failed to normalize comment data")
    
    def _map_content_type(self, instagram_type: str) -> str:
        """Map Instagram content types to standard format"""
        type_mapping = {
            'GraphImage': 'photo',
            'GraphVideo': 'video',
            'GraphSidecar': 'carousel',
            'IMAGE': 'photo',
            'VIDEO': 'video',
            'CAROUSEL_ALBUM': 'carousel'
        }
        return type_mapping.get(instagram_type, 'photo')