from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy.dialects.postgresql import JSON, UUID
import uuid
from app import db

class TaskStatus(Enum):
    """Collection task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10

class CollectionTask(db.Model):
    """Collection task tracking"""
    
    __tablename__ = 'collection_tasks'
    
    id = db.Column(db.BigInteger, primary_key=True)
    task_id = db.Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    influencer_id = db.Column(db.BigInteger, db.ForeignKey('influencers.id'), nullable=False, index=True)
    platform = db.Column(db.Enum(Platform), nullable=False)
    
    # Task configuration
    collection_type = db.Column(db.String(50), nullable=False)  # posts, comments, metrics
    parameters = db.Column(JSON)  # Collection parameters
    
    # Status tracking
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.NORMAL, index=True)
    
    # Execution tracking
    worker_id = db.Column(db.String(100))  # Celery worker ID
    started_at = db.Column(db.DateTime, index=True)
    completed_at = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Float)
    
    # Results
    items_collected = db.Column(db.Integer, default=0)
    items_failed = db.Column(db.Integer, default=0)
    result_data = db.Column(JSON)  # Collection results
    
    # Error handling
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Rate limiting
    rate_limit_hit = db.Column(db.Boolean, default=False)
    next_retry_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    error_logs = db.relationship('TaskErrorLog', backref='task', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_task_status_priority', 'status', 'priority'),
        db.Index('idx_task_platform_date', 'platform', 'created_at'),
        db.Index('idx_task_retry_schedule', 'next_retry_at'),
    )
    
    def __repr__(self):
        return f'<CollectionTask {self.task_id}: {self.status.value}>'
    
    def mark_started(self, worker_id: str):
        """Mark task as started"""
        self.status = TaskStatus.RUNNING
        self.worker_id = worker_id
        self.started_at = datetime.utcnow()
        db.session.commit()
    
    def mark_completed(self, items_collected: int = 0, result_data: dict = None):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.items_collected = items_collected
        self.result_data = result_data or {}
        
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        
        db.session.commit()
    
    def mark_failed(self, error_message: str, error_traceback: str = None, 
                   can_retry: bool = True):
        """Mark task as failed"""
        self.error_message = error_message
        self.error_traceback = error_traceback
        
        if can_retry and self.retry_count < self.max_retries:
            self.status = TaskStatus.RETRY
            self.retry_count += 1
            # Exponential backoff: 2^retry_count minutes
            delay_minutes = 2 ** self.retry_count
            self.next_retry_at = datetime.utcnow() + timedelta(minutes=delay_minutes)
        else:
            self.status = TaskStatus.FAILED
        
        db.session.commit()
    
    def can_retry_now(self) -> bool:
        """Check if task can be retried now"""
        return (
            self.status == TaskStatus.RETRY and
            self.next_retry_at and
            datetime.utcnow() >= self.next_retry_at
        )
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': str(self.task_id),
            'influencer_id': self.influencer_id,
            'platform': self.platform.value,
            'collection_type': self.collection_type,
            'parameters': self.parameters,
            'status': self.status.value,
            'priority': self.priority.value,
            'worker_id': self.worker_id,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'items_collected': self.items_collected,
            'items_failed': self.items_failed,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat()
        }

class TaskErrorLog(db.Model):
    """Detailed error logging for tasks"""
    
    __tablename__ = 'task_error_logs'
    
    id = db.Column(db.BigInteger, primary_key=True)
    task_id = db.Column(db.BigInteger, db.ForeignKey('collection_tasks.id'), nullable=False, index=True)
    
    # Error details
    error_type = db.Column(db.String(100), nullable=False)
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    
    # Context
    context_data = db.Column(JSON)  # Additional context when error occurred
    retry_attempt = db.Column(db.Integer, default=0)
    
    # Timestamp
    occurred_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'error_type': self.error_type,
            'error_message': self.error_message,
            'context_data': self.context_data,
            'retry_attempt': self.retry_attempt,
            'occurred_at': self.occurred_at.isoformat()
        }

class ProxyPool(db.Model):
    """Proxy pool management"""
    
    __tablename__ = 'proxy_pool'
    
    id = db.Column(db.Integer, primary_key=True)
    host = db.Column(db.String(255), nullable=False)
    port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(100))
    password = db.Column(db.String(255))  # Encrypted
    protocol = db.Column(db.String(10), default='http')  # http, socks5
    
    # Status tracking
    is_active = db.Column(db.Boolean, default=True, index=True)
    success_rate = db.Column(db.Float, default=1.0)  # 0.0 to 1.0
    last_used = db.Column(db.DateTime)
    last_success = db.Column(db.DateTime)
    last_failure = db.Column(db.DateTime)
    
    # Performance metrics
    avg_response_time = db.Column(db.Float, default=0.0)  # milliseconds
    total_requests = db.Column(db.BigInteger, default=0)
    successful_requests = db.Column(db.BigInteger, default=0)
    failed_requests = db.Column(db.BigInteger, default=0)
    
    # Rate limiting per proxy
    requests_today = db.Column(db.Integer, default=0)
    daily_limit = db.Column(db.Integer, default=1000)
    
    # Metadata
    provider = db.Column(db.String(100))  # Proxy provider
    location = db.Column(db.String(100))  # Proxy location
    notes = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('host', 'port', name='uq_proxy_host_port'),
        db.Index('idx_proxy_active_success', 'is_active', 'success_rate'),
    )
    
    def __repr__(self):
        return f'<Proxy {self.host}:{self.port}>'
    
    def record_usage(self, success: bool, response_time: float = None):
        """Record proxy usage statistics"""
        self.last_used = datetime.utcnow()
        self.total_requests += 1
        self.requests_today += 1
        
        if success:
            self.successful_requests += 1
            self.last_success = datetime.utcnow()
            if response_time:
                # Update average response time (moving average)
                if self.avg_response_time == 0:
                    self.avg_response_time = response_time
                else:
                    self.avg_response_time = (self.avg_response_time * 0.8) + (response_time * 0.2)
        else:
            self.failed_requests += 1
            self.last_failure = datetime.utcnow()
        
        # Update success rate
        self.success_rate = self.successful_requests / self.total_requests
        
        # Deactivate proxy if success rate too low
        if self.success_rate < 0.3 and self.total_requests > 10:
            self.is_active = False
        
        db.session.commit()
    
    def is_available(self) -> bool:
        """Check if proxy is available for use"""
        return (
            self.is_active and
            self.requests_today < self.daily_limit and
            self.success_rate > 0.3
        )
    
    def get_proxy_url(self) -> str:
        """Get formatted proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'is_active': self.is_active,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'requests_today': self.requests_today,
            'daily_limit': self.daily_limit,
            'provider': self.provider,
            'location': self.location,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'created_at': self.created_at.isoformat()
        }

class RateLimit(db.Model):
    """Rate limiting tracking per platform/endpoint"""
    
    __tablename__ = 'rate_limits'
    
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.Enum(Platform), nullable=False)
    endpoint = db.Column(db.String(100), nullable=False)
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxy_pool.id'))
    
    # Rate limit configuration
    requests_per_hour = db.Column(db.Integer, nullable=False)
    requests_per_day = db.Column(db.Integer, nullable=False)
    
    # Current usage
    current_hour_count = db.Column(db.Integer, default=0)
    current_day_count = db.Column(db.Integer, default=0)
    
    # Reset tracking
    hour_reset_at = db.Column(db.DateTime, nullable=False)
    day_reset_at = db.Column(db.DateTime, nullable=False)
    
    # Last request
    last_request_at = db.Column(db.DateTime)
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('platform', 'endpoint', 'proxy_id', name='uq_rate_limit'),
        db.Index('idx_rate_limit_reset', 'hour_reset_at', 'day_reset_at'),
    )
    
    def can_make_request(self) -> bool:
        """Check if we can make a request within rate limits"""
        now = datetime.utcnow()
        
        # Reset counters if time has passed
        if now >= self.hour_reset_at:
            self.current_hour_count = 0
            self.hour_reset_at = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        if now >= self.day_reset_at:
            self.current_day_count = 0
            self.day_reset_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Check limits
        return (
            self.current_hour_count < self.requests_per_hour and
            self.current_day_count < self.requests_per_day
        )
    
    def record_request(self):
        """Record a request against rate limits"""
        self.current_hour_count += 1
        self.current_day_count += 1
        self.last_request_at = datetime.utcnow()
        db.session.commit()
    
    def time_until_next_request(self) -> int:
        """Get seconds until next request can be made"""
        if self.current_hour_count >= self.requests_per_hour:
            return int((self.hour_reset_at - datetime.utcnow()).total_seconds())
        return 0

# Import Platform enum from influencer model
from .influencer import Platform