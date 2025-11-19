import stripe
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app

from app.models.user import User
from app.models.payment import (
    Subscription, SubscriptionPlan, Payment, PaymentStatus, 
    PlanType, SubscriptionStatus
)
from app import db

logger = logging.getLogger(__name__)

class PaymentService:
    """Service for handling payments and subscriptions with Stripe"""
    
    def __init__(self):
        # Initialize Stripe with API key from config
        stripe.api_key = current_app.config.get('STRIPE_SECRET_KEY')
        self.webhook_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        # Plan configurations
        self.plan_configs = {
            PlanType.STARTER: {
                'name': 'Starter Plan',
                'price': 29.99,
                'influencer_limit': 100,
                'posts_per_month': 10000,
                'analytics_retention_days': 30,
                'features': [
                    'Basic analytics',
                    'Up to 100 influencers',
                    '10K posts analysis per month',
                    '30 days data retention',
                    'Email support'
                ]
            },
            PlanType.PROFESSIONAL: {
                'name': 'Professional Plan',
                'price': 79.99,
                'influencer_limit': 500,
                'posts_per_month': 50000,
                'analytics_retention_days': 90,
                'features': [
                    'Advanced analytics',
                    'Up to 500 influencers',
                    '50K posts analysis per month',
                    '90 days data retention',
                    'Sentiment analysis',
                    'Trending topics',
                    'Priority support'
                ]
            },
            PlanType.ENTERPRISE: {
                'name': 'Enterprise Plan',
                'price': 199.99,
                'influencer_limit': -1,  # Unlimited
                'posts_per_month': -1,   # Unlimited
                'analytics_retention_days': 365,
                'features': [
                    'Full analytics suite',
                    'Unlimited influencers',
                    'Unlimited posts analysis',
                    '1 year data retention',
                    'Advanced sentiment analysis',
                    'Competitor analysis',
                    'Custom reports',
                    'API access',
                    '24/7 dedicated support'
                ]
            }
        }
    
    def create_stripe_customer(self, user: User) -> str:
        """Create Stripe customer for user"""
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.username,
                metadata={
                    'user_id': str(user.id),
                    'username': user.username
                }
            )
            
            # Update user with Stripe customer ID
            user.stripe_customer_id = customer.id
            db.session.commit()
            
            logger.info(f"Created Stripe customer {customer.id} for user {user.id}")
            return customer.id
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise Exception(f"Payment system error: {str(e)}")
    
    def create_payment_intent(self, user: User, plan_type: PlanType, 
                            payment_method: str = None) -> Dict[str, Any]:
        """Create payment intent for subscription"""
        try:
            # Get or create Stripe customer
            customer_id = user.stripe_customer_id
            if not customer_id:
                customer_id = self.create_stripe_customer(user)
            
            plan_config = self.plan_configs[plan_type]
            amount = int(plan_config['price'] * 100)  # Convert to cents
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency='usd',
                customer=customer_id,
                payment_method=payment_method,
                confirmation_method='manual',
                confirm=True if payment_method else False,
                metadata={
                    'user_id': str(user.id),
                    'plan_type': plan_type.value,
                    'type': 'subscription'
                }
            )
            
            # Create payment record
            payment = Payment(
                user_id=user.id,
                stripe_payment_intent_id=payment_intent.id,
                amount=plan_config['price'],
                currency='USD',
                plan_type=plan_type,
                status=PaymentStatus.PENDING
            )
            db.session.add(payment)
            db.session.commit()
            
            return {
                'client_secret': payment_intent.client_secret,
                'payment_intent_id': payment_intent.id,
                'amount': amount,
                'currency': 'usd'
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment intent: {e}")
            raise Exception(f"Payment processing error: {str(e)}")
    
    def create_subscription(self, user: User, plan_type: PlanType) -> Subscription:
        """Create subscription for user"""
        try:
            # Get or create Stripe customer
            customer_id = user.stripe_customer_id
            if not customer_id:
                customer_id = self.create_stripe_customer(user)
            
            # Create subscription plan if it doesn't exist
            plan = self.get_or_create_plan(plan_type)
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': plan.stripe_price_id}],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
                metadata={
                    'user_id': str(user.id),
                    'plan_type': plan_type.value
                }
            )
            
            # Create subscription record
            subscription = Subscription(
                user_id=user.id,
                plan_id=plan.id,
                stripe_subscription_id=stripe_subscription.id,
                status=SubscriptionStatus.INCOMPLETE,
                current_period_start=datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                ),
                current_period_end=datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                )
            )
            
            db.session.add(subscription)
            db.session.commit()
            
            logger.info(f"Created subscription {subscription.id} for user {user.id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            db.session.rollback()
            raise Exception(f"Subscription creation failed: {str(e)}")
    
    def get_or_create_plan(self, plan_type: PlanType) -> SubscriptionPlan:
        """Get existing plan or create new one"""
        plan = SubscriptionPlan.query.filter_by(plan_type=plan_type).first()
        
        if not plan:
            # Create plan in database and Stripe
            plan_config = self.plan_configs[plan_type]
            
            # Create Stripe product
            product = stripe.Product.create(
                name=plan_config['name'],
                metadata={
                    'plan_type': plan_type.value
                }
            )
            
            # Create Stripe price
            price = stripe.Price.create(
                unit_amount=int(plan_config['price'] * 100),
                currency='usd',
                recurring={'interval': 'month'},
                product=product.id,
                metadata={
                    'plan_type': plan_type.value
                }
            )
            
            # Create plan record
            plan = SubscriptionPlan(
                plan_type=plan_type,
                name=plan_config['name'],
                price=plan_config['price'],
                stripe_product_id=product.id,
                stripe_price_id=price.id,
                influencer_limit=plan_config['influencer_limit'],
                posts_per_month=plan_config['posts_per_month'],
                analytics_retention_days=plan_config['analytics_retention_days'],
                features=plan_config['features']
            )
            
            db.session.add(plan)
            db.session.commit()
            
            logger.info(f"Created new plan: {plan_type.value}")
        
        return plan
    
    def confirm_payment(self, payment_intent_id: str) -> bool:
        """Confirm payment and activate subscription"""
        try:
            # Get payment intent from Stripe
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            # Find payment record
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if not payment:
                logger.error(f"Payment record not found for intent {payment_intent_id}")
                return False
            
            if payment_intent.status == 'succeeded':
                # Update payment status
                payment.status = PaymentStatus.SUCCEEDED
                payment.paid_at = datetime.utcnow()
                
                # Activate subscription if this is a subscription payment
                if payment.plan_type:
                    self.activate_subscription(payment.user, payment.plan_type)
                
                db.session.commit()
                
                logger.info(f"Payment confirmed: {payment_intent_id}")
                return True
            else:
                logger.warning(f"Payment not succeeded: {payment_intent.status}")
                return False
                
        except stripe.error.StripeError as e:
            logger.error(f"Failed to confirm payment: {e}")
            return False
    
    def activate_subscription(self, user: User, plan_type: PlanType):
        """Activate subscription for user"""
        try:
            # Deactivate any existing subscriptions
            existing_subscriptions = Subscription.query.filter_by(
                user_id=user.id,
                status=SubscriptionStatus.ACTIVE
            ).all()
            
            for sub in existing_subscriptions:
                sub.status = SubscriptionStatus.CANCELLED
                sub.cancelled_at = datetime.utcnow()
            
            # Find the new subscription
            plan = self.get_or_create_plan(plan_type)
            subscription = Subscription.query.filter_by(
                user_id=user.id,
                plan_id=plan.id,
                status=SubscriptionStatus.INCOMPLETE
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.ACTIVE
                subscription.activated_at = datetime.utcnow()
                
                # Update user subscription info
                user.current_plan = plan_type
                user.subscription_expires_at = subscription.current_period_end
                
                db.session.commit()
                
                logger.info(f"Activated subscription for user {user.id}")
            
        except Exception as e:
            logger.error(f"Failed to activate subscription: {e}")
            db.session.rollback()
    
    def cancel_subscription(self, user: User) -> bool:
        """Cancel user's active subscription"""
        try:
            # Find active subscription
            subscription = Subscription.query.filter_by(
                user_id=user.id,
                status=SubscriptionStatus.ACTIVE
            ).first()
            
            if not subscription:
                logger.warning(f"No active subscription found for user {user.id}")
                return False
            
            # Cancel in Stripe
            stripe.Subscription.modify(
                subscription.stripe_subscription_id,
                cancel_at_period_end=True
            )
            
            # Update subscription status
            subscription.status = SubscriptionStatus.CANCELLED
            subscription.cancelled_at = datetime.utcnow()
            
            # Update user info
            user.current_plan = PlanType.FREE
            user.subscription_expires_at = subscription.current_period_end
            
            db.session.commit()
            
            logger.info(f"Cancelled subscription for user {user.id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription: {e}")
            return False
    
    def handle_webhook(self, payload: str, signature: str) -> bool:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            event_type = event['type']
            event_data = event['data']['object']
            
            logger.info(f"Processing webhook event: {event_type}")
            
            if event_type == 'payment_intent.succeeded':
                self.handle_payment_succeeded(event_data)
            elif event_type == 'payment_intent.payment_failed':
                self.handle_payment_failed(event_data)
            elif event_type == 'invoice.payment_succeeded':
                self.handle_invoice_payment_succeeded(event_data)
            elif event_type == 'customer.subscription.updated':
                self.handle_subscription_updated(event_data)
            elif event_type == 'customer.subscription.deleted':
                self.handle_subscription_deleted(event_data)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
            
            return True
            
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return False
        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return False
    
    def handle_payment_succeeded(self, payment_intent_data: Dict):
        """Handle successful payment"""
        try:
            payment_intent_id = payment_intent_data['id']
            
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment:
                payment.status = PaymentStatus.SUCCEEDED
                payment.paid_at = datetime.utcnow()
                
                if payment.plan_type:
                    self.activate_subscription(payment.user, payment.plan_type)
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")
            db.session.rollback()
    
    def handle_payment_failed(self, payment_intent_data: Dict):
        """Handle failed payment"""
        try:
            payment_intent_id = payment_intent_data['id']
            
            payment = Payment.query.filter_by(
                stripe_payment_intent_id=payment_intent_id
            ).first()
            
            if payment:
                payment.status = PaymentStatus.FAILED
                payment.failure_reason = payment_intent_data.get('last_payment_error', {}).get('message', 'Unknown error')
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")
            db.session.rollback()
    
    def handle_invoice_payment_succeeded(self, invoice_data: Dict):
        """Handle successful recurring payment"""
        try:
            subscription_id = invoice_data.get('subscription')
            if not subscription_id:
                return
            
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                # Update subscription period
                stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                subscription.current_period_start = datetime.fromtimestamp(
                    stripe_subscription.current_period_start
                )
                subscription.current_period_end = datetime.fromtimestamp(
                    stripe_subscription.current_period_end
                )
                
                # Update user subscription expiry
                subscription.user.subscription_expires_at = subscription.current_period_end
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error handling invoice payment: {e}")
            db.session.rollback()
    
    def handle_subscription_updated(self, subscription_data: Dict):
        """Handle subscription updates"""
        try:
            subscription_id = subscription_data['id']
            
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                # Update subscription status based on Stripe status
                stripe_status = subscription_data.get('status')
                
                if stripe_status == 'active':
                    subscription.status = SubscriptionStatus.ACTIVE
                elif stripe_status == 'canceled':
                    subscription.status = SubscriptionStatus.CANCELLED
                    subscription.cancelled_at = datetime.utcnow()
                elif stripe_status == 'past_due':
                    subscription.status = SubscriptionStatus.PAST_DUE
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")
            db.session.rollback()
    
    def handle_subscription_deleted(self, subscription_data: Dict):
        """Handle subscription deletion"""
        try:
            subscription_id = subscription_data['id']
            
            subscription = Subscription.query.filter_by(
                stripe_subscription_id=subscription_id
            ).first()
            
            if subscription:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = datetime.utcnow()
                
                # Revert user to free plan
                subscription.user.current_plan = PlanType.FREE
                subscription.user.subscription_expires_at = None
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {e}")
            db.session.rollback()
    
    def get_subscription_info(self, user: User) -> Dict[str, Any]:
        """Get user's subscription information"""
        try:
            current_subscription = Subscription.query.filter_by(
                user_id=user.id,
                status=SubscriptionStatus.ACTIVE
            ).first()
            
            if current_subscription:
                plan = current_subscription.plan
                days_remaining = (current_subscription.current_period_end - datetime.utcnow()).days
                
                return {
                    'has_active_subscription': True,
                    'plan': {
                        'name': plan.name,
                        'type': plan.plan_type.value,
                        'price': plan.price,
                        'features': plan.features
                    },
                    'current_period_end': current_subscription.current_period_end.isoformat(),
                    'days_remaining': max(days_remaining, 0),
                    'auto_renew': True  # Assume auto-renew unless cancelled
                }
            else:
                return {
                    'has_active_subscription': False,
                    'plan': {
                        'name': 'Free Plan',
                        'type': 'free',
                        'price': 0,
                        'features': [
                            'Basic dashboard',
                            'Up to 10 influencers',
                            '1K posts analysis per month',
                            '7 days data retention'
                        ]
                    }
                }
                
        except Exception as e:
            logger.error(f"Error getting subscription info: {e}")
            return {'has_active_subscription': False}
    
    def get_usage_stats(self, user: User) -> Dict[str, Any]:
        """Get user's current usage statistics"""
        try:
            # This would integrate with analytics service to get real usage
            # For now, returning mock data
            
            plan_config = self.plan_configs.get(user.current_plan, {})
            
            return {
                'influencers_tracked': 45,  # Would come from database
                'influencer_limit': plan_config.get('influencer_limit', 10),
                'posts_analyzed_this_month': 8500,  # Would come from analytics
                'posts_limit_per_month': plan_config.get('posts_per_month', 1000),
                'storage_used_gb': 2.3,  # Would calculate from data storage
                'api_calls_this_month': 1250  # Would track API usage
            }
            
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {}
    
    def get_available_plans(self) -> List[Dict[str, Any]]:
        """Get all available subscription plans"""
        plans = []
        
        for plan_type, config in self.plan_configs.items():
            plans.append({
                'type': plan_type.value,
                'name': config['name'],
                'price': config['price'],
                'influencer_limit': config['influencer_limit'],
                'posts_per_month': config['posts_per_month'],
                'analytics_retention_days': config['analytics_retention_days'],
                'features': config['features'],
                'recommended': plan_type == PlanType.PROFESSIONAL  # Mark professional as recommended
            })
        
        return plans