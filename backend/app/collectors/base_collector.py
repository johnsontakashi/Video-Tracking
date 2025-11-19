import asyncio
import aiohttp
import random
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging
import hashlib
import json

from app.models.collection import ProxyPool, RateLimit, TaskErrorLog
from app.models.influencer import Platform
from app import db

logger = logging.getLogger(__name__)

class CollectionError(Exception):
    """Base exception for collection errors"""
    pass

class RateLimitError(CollectionError):
    """Rate limit exceeded error"""
    def __init__(self, message: str, retry_after: int = None):
        self.retry_after = retry_after
        super().__init__(message)

class ProxyError(CollectionError):
    """Proxy-related error"""
    pass

class AuthenticationError(CollectionError):
    """Authentication failed error"""
    pass

@dataclass
class CollectionResult:
    """Result of a collection operation"""
    success: bool
    data: List[Dict] = None
    error: str = None
    items_collected: int = 0
    rate_limited: bool = False
    retry_after: int = None
    proxy_failed: bool = False

class ProxyManager:
    """Advanced proxy management with rotation and health checking"""
    
    def __init__(self):
        self.current_proxy = None
        self.failed_proxies = set()
        self.proxy_usage = {}  # Track usage per proxy
        
    async def get_available_proxy(self) -> Optional[ProxyPool]:
        """Get an available proxy from the pool"""
        proxies = ProxyPool.query.filter_by(is_active=True).filter(
            ProxyPool.success_rate > 0.3
        ).order_by(ProxyPool.last_used.asc()).all()
        
        available_proxies = [p for p in proxies if p.is_available() 
                           and p.id not in self.failed_proxies]
        
        if not available_proxies:
            # Reset failed proxies if all are failed
            if len(self.failed_proxies) == len(proxies):
                self.failed_proxies.clear()
                available_proxies = [p for p in proxies if p.is_available()]
        
        if available_proxies:
            # Choose proxy with least recent usage
            return min(available_proxies, 
                      key=lambda p: self.proxy_usage.get(p.id, 0))
        
        return None
    
    async def test_proxy(self, proxy: ProxyPool) -> bool:
        """Test if proxy is working"""
        try:
            proxy_url = proxy.get_proxy_url()
            
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10),
                    ssl=False
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        proxy.record_usage(True, response_time)
                        return True
                    else:
                        proxy.record_usage(False)
                        return False
                        
        except Exception as e:
            logger.warning(f"Proxy test failed for {proxy.host}:{proxy.port}: {e}")
            proxy.record_usage(False)
            return False
    
    async def rotate_proxy(self, failed_proxy_id: int = None):
        """Rotate to a new proxy"""
        if failed_proxy_id:
            self.failed_proxies.add(failed_proxy_id)
        
        self.current_proxy = await self.get_available_proxy()
        if self.current_proxy:
            # Test new proxy before using
            is_working = await self.test_proxy(self.current_proxy)
            if not is_working:
                self.failed_proxies.add(self.current_proxy.id)
                return await self.rotate_proxy()
        
        return self.current_proxy
    
    def record_proxy_usage(self, proxy_id: int, success: bool):
        """Record proxy usage statistics"""
        if proxy_id not in self.proxy_usage:
            self.proxy_usage[proxy_id] = 0
        self.proxy_usage[proxy_id] += 1

class RateLimitManager:
    """Rate limit management for different platforms and endpoints"""
    
    def __init__(self, platform: Platform):
        self.platform = platform
        self.rate_limits = self._load_rate_limits()
    
    def _load_rate_limits(self) -> Dict[str, RateLimit]:
        """Load rate limits from database"""
        limits = RateLimit.query.filter_by(platform=self.platform).all()
        return {limit.endpoint: limit for limit in limits}
    
    async def can_make_request(self, endpoint: str, proxy_id: int = None) -> Tuple[bool, int]:
        """
        Check if we can make a request to endpoint
        Returns (can_make_request, seconds_to_wait)
        """
        rate_limit = self.rate_limits.get(endpoint)
        if not rate_limit:
            # Create default rate limit if not exists
            rate_limit = self._create_default_rate_limit(endpoint, proxy_id)
        
        can_request = rate_limit.can_make_request()
        wait_time = rate_limit.time_until_next_request()
        
        return can_request, wait_time
    
    def _create_default_rate_limit(self, endpoint: str, proxy_id: int = None) -> RateLimit:
        """Create default rate limit for endpoint"""
        defaults = {
            'instagram': {'requests_per_hour': 200, 'requests_per_day': 4000},
            'youtube': {'requests_per_hour': 1000, 'requests_per_day': 50000},
            'tiktok': {'requests_per_hour': 100, 'requests_per_day': 2000},
            'twitter': {'requests_per_hour': 300, 'requests_per_day': 7200}
        }
        
        default = defaults.get(self.platform.value, {'requests_per_hour': 100, 'requests_per_day': 1000})
        
        now = datetime.utcnow()
        rate_limit = RateLimit(
            platform=self.platform,
            endpoint=endpoint,
            proxy_id=proxy_id,
            requests_per_hour=default['requests_per_hour'],
            requests_per_day=default['requests_per_day'],
            hour_reset_at=now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1),
            day_reset_at=now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        )
        
        db.session.add(rate_limit)
        db.session.commit()
        
        self.rate_limits[endpoint] = rate_limit
        return rate_limit
    
    async def record_request(self, endpoint: str, proxy_id: int = None):
        """Record a request against rate limits"""
        rate_limit = self.rate_limits.get(endpoint)
        if rate_limit:
            rate_limit.record_request()

class BaseCollector(ABC):
    """Abstract base class for all platform collectors"""
    
    def __init__(self, platform: Platform):
        self.platform = platform
        self.proxy_manager = ProxyManager()
        self.rate_limit_manager = RateLimitManager(platform)
        self.session = None
        self.max_retries = 3
        self.retry_delay = 1  # Base retry delay in seconds
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform API"""
        pass
    
    @abstractmethod
    async def collect_influencer_data(self, username: str) -> Dict:
        """Collect basic influencer profile data"""
        pass
    
    @abstractmethod
    async def collect_posts(self, influencer_id: str, limit: int = 50) -> List[Dict]:
        """Collect posts for an influencer"""
        pass
    
    @abstractmethod
    async def collect_comments(self, post_id: str, limit: int = 100) -> List[Dict]:
        """Collect comments for a post"""
        pass
    
    @abstractmethod
    def normalize_influencer_data(self, raw_data: Dict) -> Dict:
        """Normalize raw influencer data to standard format"""
        pass
    
    @abstractmethod
    def normalize_post_data(self, raw_data: Dict) -> Dict:
        """Normalize raw post data to standard format"""
        pass
    
    @abstractmethod
    def normalize_comment_data(self, raw_data: Dict) -> Dict:
        """Normalize raw comment data to standard format"""
        pass
    
    async def make_request(self, endpoint: str, url: str, method: str = 'GET', 
                          **kwargs) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """
        Make HTTP request with proxy rotation and rate limiting
        Returns (success, data, error_message)
        """
        for attempt in range(self.max_retries):
            try:
                # Check rate limits
                can_request, wait_time = await self.rate_limit_manager.can_make_request(
                    endpoint, self.proxy_manager.current_proxy.id if self.proxy_manager.current_proxy else None
                )
                
                if not can_request:
                    if wait_time > 0:
                        logger.info(f"Rate limited, waiting {wait_time} seconds")
                        await asyncio.sleep(min(wait_time, 300))  # Max wait 5 minutes
                    return False, None, f"Rate limited, retry after {wait_time}s"
                
                # Get proxy if not set
                if not self.proxy_manager.current_proxy:
                    await self.proxy_manager.rotate_proxy()
                
                # Prepare request
                request_kwargs = kwargs.copy()
                if self.proxy_manager.current_proxy:
                    request_kwargs['proxy'] = self.proxy_manager.current_proxy.get_proxy_url()
                
                # Add headers
                headers = request_kwargs.get('headers', {})
                headers.update(self._get_default_headers())
                request_kwargs['headers'] = headers
                
                # Make request
                start_time = time.time()
                async with self.session.request(method, url, **request_kwargs) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    # Record successful proxy usage
                    if self.proxy_manager.current_proxy:
                        self.proxy_manager.current_proxy.record_usage(True, response_time)
                        self.proxy_manager.record_proxy_usage(
                            self.proxy_manager.current_proxy.id, True
                        )
                    
                    # Record successful request
                    await self.rate_limit_manager.record_request(
                        endpoint, 
                        self.proxy_manager.current_proxy.id if self.proxy_manager.current_proxy else None
                    )
                    
                    # Handle response
                    if response.status == 200:
                        try:
                            data = await response.json()
                            return True, data, None
                        except json.JSONDecodeError:
                            text = await response.text()
                            return True, {'raw_response': text}, None
                    
                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        return False, None, f"Rate limited by platform, retry after {retry_after}s"
                    
                    elif response.status in [401, 403]:  # Authentication error
                        return False, None, f"Authentication failed: {response.status}"
                    
                    elif response.status >= 500:  # Server error, retry
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(self.retry_delay * (2 ** attempt))
                            continue
                        return False, None, f"Server error: {response.status}"
                    
                    else:
                        return False, None, f"HTTP {response.status}: {await response.text()}"
            
            except aiohttp.ClientProxyConnectionError as e:
                # Proxy failed, rotate and retry
                logger.warning(f"Proxy failed: {e}")
                if self.proxy_manager.current_proxy:
                    self.proxy_manager.current_proxy.record_usage(False)
                    await self.proxy_manager.rotate_proxy(self.proxy_manager.current_proxy.id)
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return False, None, f"Proxy connection failed after {self.max_retries} attempts"
            
            except asyncio.TimeoutError:
                logger.warning(f"Request timeout on attempt {attempt + 1}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return False, None, f"Request timeout after {self.max_retries} attempts"
            
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                return False, None, f"Unexpected error: {str(e)}"
        
        return False, None, f"Failed after {self.max_retries} attempts"
    
    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for requests"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def collect_with_pagination(self, collect_func, max_items: int = 1000) -> List[Dict]:
        """Helper method for paginated collection"""
        all_items = []
        cursor = None
        
        while len(all_items) < max_items:
            try:
                items, next_cursor = await collect_func(cursor)
                
                if not items:
                    break
                
                all_items.extend(items)
                
                if not next_cursor or len(items) == 0:
                    break
                    
                cursor = next_cursor
                
                # Rate limiting between pages
                await asyncio.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Pagination error: {e}")
                break
        
        return all_items[:max_items]
    
    def generate_request_id(self, *args) -> str:
        """Generate unique request ID for caching/deduplication"""
        content = f"{self.platform.value}_{int(time.time())}_{random.randint(1000, 9999)}"
        for arg in args:
            content += f"_{str(arg)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def health_check(self) -> bool:
        """Check if collector is healthy and can make requests"""
        try:
            return await self.authenticate()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        return {
            'platform': self.platform.value,
            'current_proxy': self.proxy_manager.current_proxy.host if self.proxy_manager.current_proxy else None,
            'failed_proxies': len(self.proxy_manager.failed_proxies),
            'proxy_usage': self.proxy_manager.proxy_usage
        }