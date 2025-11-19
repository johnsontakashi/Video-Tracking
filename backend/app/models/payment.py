from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSON
from app import db

class PlanType(Enum):
    """Subscription plan types"""
    FREE = "free"
    STARTER = "starter" 
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class SubscriptionStatus(Enum):
    """Subscription status"""
    INCOMPLETE = "incomplete"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELLED = "cancelled"
    UNPAID = "unpaid"

class PaymentStatus(Enum):
    """Payment status"""
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class SubscriptionPlan(db.Model):
    """Subscription plan definitions"""
    
    __tablename__ = 'subscription_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    plan_type = db.Column(db.Enum(PlanType), nullable=False, unique=True, index=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Stripe integration
    stripe_product_id = db.Column(db.String(100), unique=True)
    stripe_price_id = db.Column(db.String(100), unique=True)
    
    # Plan limits
    influencer_limit = db.Column(db.Integer, default=-1)  # -1 for unlimited
    posts_per_month = db.Column(db.Integer, default=-1)   # -1 for unlimited
    analytics_retention_days = db.Column(db.Integer, default=30)
    
    # Features
    features = db.Column(JSON)  # List of features included
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='plan', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='subscription_plan', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SubscriptionPlan {self.name}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'plan_type': self.plan_type.value,
            'name': self.name,
            'price': float(self.price),
            'influencer_limit': self.influencer_limit,
            'posts_per_month': self.posts_per_month,
            'analytics_retention_days': self.analytics_retention_days,
            'features': self.features,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

class Subscription(db.Model):
    """User subscriptions"""
    
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False, index=True)
    
    # Stripe integration
    stripe_subscription_id = db.Column(db.String(100), unique=True, index=True)
    stripe_customer_id = db.Column(db.String(100), index=True)
    
    # Subscription details
    status = db.Column(db.Enum(SubscriptionStatus), nullable=False, index=True)
    
    # Billing period
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False, index=True)
    
    # Trial period
    trial_start = db.Column(db.DateTime)
    trial_end = db.Column(db.DateTime)
    
    # Status timestamps
    activated_at = db.Column(db.DateTime)
    cancelled_at = db.Column(db.DateTime)
    
    # Usage tracking
    usage_data = db.Column(JSON)  # Track monthly usage
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_subscription_user_status', 'user_id', 'status'),
        db.Index('idx_subscription_period', 'current_period_end'),
    )
    
    def __repr__(self):
        return f'<Subscription {self.id}: {self.status.value}>'
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return (
            self.status == SubscriptionStatus.ACTIVE and
            self.current_period_end > datetime.utcnow()
        )
    
    def days_remaining(self) -> int:
        """Get days remaining in current period"""
        if not self.is_active():
            return 0
        return max(0, (self.current_period_end - datetime.utcnow()).days)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan.to_dict() if self.plan else None,
            'status': self.status.value,
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'activated_at': self.activated_at.isoformat() if self.activated_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'is_active': self.is_active(),
            'days_remaining': self.days_remaining(),
            'usage_data': self.usage_data,
            'created_at': self.created_at.isoformat()
        }

class Payment(db.Model):
    """Payment records"""
    
    __tablename__ = 'payments'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = db.Column(db.BigInteger, db.ForeignKey('subscriptions.id'), index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), index=True)
    
    # Stripe integration
    stripe_payment_intent_id = db.Column(db.String(100), unique=True, index=True)
    stripe_invoice_id = db.Column(db.String(100), index=True)
    
    # Payment details
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    status = db.Column(db.Enum(PaymentStatus), nullable=False, index=True)
    
    # Payment type
    plan_type = db.Column(db.Enum(PlanType), index=True)  # For subscription payments
    description = db.Column(db.String(255))
    
    # Payment method
    payment_method_type = db.Column(db.String(50))  # card, bank_transfer, etc.
    last4 = db.Column(db.String(4))  # Last 4 digits of card
    
    # Status details
    failure_reason = db.Column(db.Text)
    refund_amount = db.Column(db.Numeric(10, 2))
    refund_reason = db.Column(db.String(255))
    
    # Timestamps
    paid_at = db.Column(db.DateTime, index=True)
    failed_at = db.Column(db.DateTime)
    refunded_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        db.Index('idx_payment_user_status', 'user_id', 'status'),
        db.Index('idx_payment_date_amount', 'created_at', 'amount'),
    )
    
    def __repr__(self):
        return f'<Payment {self.id}: ${self.amount} {self.status.value}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'plan_type': self.plan_type.value if self.plan_type else None,
            'amount': float(self.amount),
            'currency': self.currency,
            'status': self.status.value,
            'description': self.description,
            'payment_method_type': self.payment_method_type,
            'last4': self.last4,
            'failure_reason': self.failure_reason,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'refunded_at': self.refunded_at.isoformat() if self.refunded_at else None,
            'created_at': self.created_at.isoformat()
        }

class UsageRecord(db.Model):
    """Track usage metrics for billing"""
    
    __tablename__ = 'usage_records'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = db.Column(db.BigInteger, db.ForeignKey('subscriptions.id'), index=True)
    
    # Usage period
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Usage metrics
    influencers_tracked = db.Column(db.Integer, default=0)
    posts_analyzed = db.Column(db.Integer, default=0)
    comments_analyzed = db.Column(db.Integer, default=0)
    api_calls_made = db.Column(db.Integer, default=0)
    storage_used_gb = db.Column(db.Float, default=0.0)
    
    # Usage by platform
    instagram_posts = db.Column(db.Integer, default=0)
    youtube_posts = db.Column(db.Integer, default=0)
    tiktok_posts = db.Column(db.Integer, default=0)
    twitter_posts = db.Column(db.Integer, default=0)
    
    # Analytics features used
    sentiment_analyses = db.Column(db.Integer, default=0)
    trend_analyses = db.Column(db.Integer, default=0)
    competitor_analyses = db.Column(db.Integer, default=0)
    
    # Timestamps
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes
    __table_args__ = (
        db.UniqueConstraint('user_id', 'period_start', 'period_end', name='uq_usage_period'),
        db.Index('idx_usage_user_period', 'user_id', 'period_start'),
    )
    
    def __repr__(self):
        return f'<UsageRecord {self.user_id}: {self.period_start} - {self.period_end}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'usage_metrics': {
                'influencers_tracked': self.influencers_tracked,
                'posts_analyzed': self.posts_analyzed,
                'comments_analyzed': self.comments_analyzed,
                'api_calls_made': self.api_calls_made,
                'storage_used_gb': self.storage_used_gb
            },
            'platform_breakdown': {
                'instagram': self.instagram_posts,
                'youtube': self.youtube_posts,
                'tiktok': self.tiktok_posts,
                'twitter': self.twitter_posts
            },
            'analytics_usage': {
                'sentiment_analyses': self.sentiment_analyses,
                'trend_analyses': self.trend_analyses,
                'competitor_analyses': self.competitor_analyses
            },
            'recorded_at': self.recorded_at.isoformat()
        }

class Invoice(db.Model):
    """Invoice records for accounting"""
    
    __tablename__ = 'invoices'
    
    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id'), nullable=False, index=True)
    subscription_id = db.Column(db.BigInteger, db.ForeignKey('subscriptions.id'), index=True)
    
    # Stripe integration
    stripe_invoice_id = db.Column(db.String(100), unique=True, index=True)
    
    # Invoice details
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    amount_total = db.Column(db.Numeric(10, 2), nullable=False)
    amount_paid = db.Column(db.Numeric(10, 2), default=0)
    amount_due = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='USD', nullable=False)
    
    # Billing period
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    
    # Status
    status = db.Column(db.String(50), nullable=False, index=True)  # draft, open, paid, void, uncollectible
    
    # Dates
    invoice_date = db.Column(db.DateTime, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    paid_date = db.Column(db.DateTime)
    
    # Invoice data
    line_items = db.Column(JSON)  # Detailed breakdown of charges
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}: ${self.amount_total}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_id': self.subscription_id,
            'invoice_number': self.invoice_number,
            'amount_total': float(self.amount_total),
            'amount_paid': float(self.amount_paid),
            'amount_due': float(self.amount_due),
            'currency': self.currency,
            'period_start': self.period_start.isoformat(),
            'period_end': self.period_end.isoformat(),
            'status': self.status,
            'invoice_date': self.invoice_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'paid_date': self.paid_date.isoformat() if self.paid_date else None,
            'line_items': self.line_items,
            'created_at': self.created_at.isoformat()
        }