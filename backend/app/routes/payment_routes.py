from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import stripe
import logging

from app.services.payment_service import PaymentService
from app.models.user import User
from app.models.payment import PlanType, Subscription, Payment, SubscriptionPlan
from app import db

logger = logging.getLogger(__name__)

payment_bp = Blueprint('payment', __name__, url_prefix='/api/payment')

# Initialize payment service
payment_service = PaymentService()

@payment_bp.route('/health', methods=['GET'])
def payment_health():
    """Check payment service health"""
    try:
        return jsonify({
            'status': 'healthy',
            'stripe_connected': bool(stripe.api_key)
        }), 200
    except Exception as e:
        logger.error(f"Payment health check failed: {e}")
        return jsonify({'error': 'Payment service unavailable'}), 500

@payment_bp.route('/plans', methods=['GET'])
def get_plans():
    """Get all available subscription plans"""
    try:
        plans = payment_service.get_available_plans()
        return jsonify({
            'plans': plans
        }), 200
    except Exception as e:
        logger.error(f"Error getting plans: {e}")
        return jsonify({'error': 'Failed to retrieve plans'}), 500

@payment_bp.route('/subscription/info', methods=['GET'])
@jwt_required()
def get_subscription_info():
    """Get current user's subscription information"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription_info = payment_service.get_subscription_info(user)
        usage_stats = payment_service.get_usage_stats(user)
        
        return jsonify({
            'subscription': subscription_info,
            'usage': usage_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting subscription info: {e}")
        return jsonify({'error': 'Failed to retrieve subscription info'}), 500

@payment_bp.route('/payment-intent', methods=['POST'])
@jwt_required()
def create_payment_intent():
    """Create payment intent for subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        plan_type_str = data.get('plan_type')
        payment_method = data.get('payment_method')
        
        if not plan_type_str:
            return jsonify({'error': 'Plan type is required'}), 400
        
        try:
            plan_type = PlanType(plan_type_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid plan type'}), 400
        
        # Create payment intent
        payment_intent_data = payment_service.create_payment_intent(
            user, plan_type, payment_method
        )
        
        return jsonify({
            'success': True,
            'payment_intent': payment_intent_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/subscription/create', methods=['POST'])
@jwt_required()
def create_subscription():
    """Create subscription for user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        plan_type_str = data.get('plan_type')
        
        if not plan_type_str:
            return jsonify({'error': 'Plan type is required'}), 400
        
        try:
            plan_type = PlanType(plan_type_str.lower())
        except ValueError:
            return jsonify({'error': 'Invalid plan type'}), 400
        
        # Create subscription
        subscription = payment_service.create_subscription(user, plan_type)
        
        return jsonify({
            'success': True,
            'message': 'Subscription created successfully',
            'subscription': subscription.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating subscription: {e}")
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/subscription/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel user's active subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        success = payment_service.cancel_subscription(user)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Subscription cancelled successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to cancel subscription'
            }), 400
            
    except Exception as e:
        logger.error(f"Error cancelling subscription: {e}")
        return jsonify({'error': 'Failed to cancel subscription'}), 500

@payment_bp.route('/payment/confirm', methods=['POST'])
@jwt_required()
def confirm_payment():
    """Confirm payment and process subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        payment_intent_id = data.get('payment_intent_id')
        
        if not payment_intent_id:
            return jsonify({'error': 'Payment intent ID is required'}), 400
        
        success = payment_service.confirm_payment(payment_intent_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Payment confirmed successfully'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Payment confirmation failed'
            }), 400
            
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        return jsonify({'error': 'Failed to confirm payment'}), 500

@payment_bp.route('/payments', methods=['GET'])
@jwt_required()
def get_user_payments():
    """Get user's payment history"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        payments = Payment.query.filter_by(user_id=user_id).order_by(
            Payment.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'payments': [payment.to_dict() for payment in payments.items],
            'pagination': {
                'page': page,
                'pages': payments.pages,
                'per_page': per_page,
                'total': payments.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user payments: {e}")
        return jsonify({'error': 'Failed to retrieve payments'}), 500

@payment_bp.route('/subscriptions', methods=['GET'])
@jwt_required()
def get_user_subscriptions():
    """Get user's subscription history"""
    try:
        user_id = get_jwt_identity()
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        subscriptions = Subscription.query.filter_by(user_id=user_id).order_by(
            Subscription.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'subscriptions': [sub.to_dict() for sub in subscriptions.items],
            'pagination': {
                'page': page,
                'pages': subscriptions.pages,
                'per_page': per_page,
                'total': subscriptions.total
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user subscriptions: {e}")
        return jsonify({'error': 'Failed to retrieve subscriptions'}), 500

@payment_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhook events"""
    try:
        payload = request.get_data(as_text=True)
        signature = request.headers.get('Stripe-Signature')
        
        if not signature:
            logger.error('Missing Stripe signature')
            return jsonify({'error': 'Missing signature'}), 400
        
        success = payment_service.handle_webhook(payload, signature)
        
        if success:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'error': 'Webhook processing failed'}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@payment_bp.route('/usage', methods=['GET'])
@jwt_required()
def get_usage_stats():
    """Get current usage statistics for the user"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        usage_stats = payment_service.get_usage_stats(user)
        
        return jsonify({
            'usage': usage_stats
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting usage stats: {e}")
        return jsonify({'error': 'Failed to retrieve usage statistics'}), 500

@payment_bp.route('/billing/portal', methods=['POST'])
@jwt_required()
def create_billing_portal():
    """Create Stripe billing portal session"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.stripe_customer_id:
            return jsonify({'error': 'Customer not found'}), 404
        
        # Create billing portal session
        session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=request.json.get('return_url', 'http://localhost:3001/dashboard')
        )
        
        return jsonify({
            'url': session.url
        }), 200
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe billing portal error: {e}")
        return jsonify({'error': 'Failed to create billing portal session'}), 500
    except Exception as e:
        logger.error(f"Error creating billing portal: {e}")
        return jsonify({'error': 'Failed to create billing portal session'}), 500

# Admin routes
@payment_bp.route('/admin/stats', methods=['GET'])
@jwt_required()
def get_payment_stats():
    """Get payment system statistics (admin only)"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        # Get payment statistics
        total_subscriptions = Subscription.query.count()
        active_subscriptions = Subscription.query.filter(
            Subscription.status == 'active'
        ).count()
        
        total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.status == 'succeeded'
        ).scalar() or 0
        
        monthly_revenue = db.session.query(db.func.sum(Payment.amount)).filter(
            Payment.status == 'succeeded',
            Payment.created_at >= db.func.date_trunc('month', db.func.current_date())
        ).scalar() or 0
        
        plan_distribution = db.session.query(
            SubscriptionPlan.name,
            db.func.count(Subscription.id)
        ).join(Subscription).filter(
            Subscription.status == 'active'
        ).group_by(SubscriptionPlan.name).all()
        
        return jsonify({
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'total_revenue': float(total_revenue),
            'monthly_revenue': float(monthly_revenue),
            'plan_distribution': dict(plan_distribution)
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting payment stats: {e}")
        return jsonify({'error': 'Failed to retrieve payment statistics'}), 500

@payment_bp.route('/admin/users/<int:user_id>/subscription', methods=['POST'])
@jwt_required()
def admin_manage_subscription(user_id):
    """Admin endpoint to manage user subscriptions"""
    try:
        current_user_id = get_jwt_identity()
        current_user = User.query.get(current_user_id)
        
        if not current_user or not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        action = data.get('action')
        
        if action == 'cancel':
            success = payment_service.cancel_subscription(target_user)
            message = 'Subscription cancelled' if success else 'Failed to cancel subscription'
        elif action == 'reactivate':
            plan_type = PlanType(data.get('plan_type', 'starter'))
            payment_service.activate_subscription(target_user, plan_type)
            success = True
            message = 'Subscription reactivated'
        else:
            return jsonify({'error': 'Invalid action'}), 400
        
        return jsonify({
            'success': success,
            'message': message
        }), 200
        
    except Exception as e:
        logger.error(f"Error managing subscription: {e}")
        return jsonify({'error': 'Failed to manage subscription'}), 500