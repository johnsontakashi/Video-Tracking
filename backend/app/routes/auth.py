from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user, get_jwt
from marshmallow import ValidationError
from app import limiter
from app.services.auth_service import AuthService
from app.models.user import UserRole
from app.utils.validators import (
    SignupSchema, LoginSchema, PasswordResetRequestSchema, 
    PasswordResetSchema, RefreshTokenSchema, ChangePasswordSchema
)
from app.middleware.auth import require_role, require_fresh_token

auth_bp = Blueprint('auth', __name__)

# Schema instances
signup_schema = SignupSchema()
login_schema = LoginSchema()
password_reset_request_schema = PasswordResetRequestSchema()
password_reset_schema = PasswordResetSchema()
refresh_token_schema = RefreshTokenSchema()
change_password_schema = ChangePasswordSchema()

@auth_bp.route('/signup', methods=['POST'])
@limiter.limit("5 per minute")
def signup():
    """
    User registration endpoint.
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "first_name": "John",
        "last_name": "Doe",
        "role": "guest"  // optional, defaults to "guest"
    }
    
    Response:
    {
        "success": true,
        "message": "User registered successfully",
        "user": {...}
    }
    """
    try:
        # Validate input
        data = signup_schema.load(request.json or {})
        
        # Register user
        success, user, error = AuthService.register_user(
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=UserRole(data.get('role', 'guest'))
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'registration_failed',
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Invalid input data',
            'details': e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Signup error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Registration failed'
        }), 500

@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    """
    User login endpoint.
    
    Request Body:
    {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "remember_me": false  // optional
    }
    
    Response:
    {
        "success": true,
        "access_token": "jwt_token",
        "refresh_token": "refresh_token",
        "token_type": "Bearer",
        "expires_in": 900,
        "user": {...}
    }
    """
    try:
        # Validate input
        data = login_schema.load(request.json or {})
        
        # Authenticate user
        success, user, tokens, error = AuthService.authenticate_user(
            email=data['email'],
            password=data['password'],
            request=request
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'authentication_failed',
                'message': error
            }), 401
        
        return jsonify({
            'success': True,
            **tokens
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Invalid input data',
            'details': e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Login failed'
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@limiter.limit("20 per minute")
def refresh():
    """
    Refresh access token endpoint.
    
    Request Body:
    {
        "refresh_token": "refresh_token_string"
    }
    
    Response:
    {
        "success": true,
        "access_token": "new_jwt_token",
        "token_type": "Bearer",
        "expires_in": 900,
        "user": {...}
    }
    """
    try:
        # Validate input
        data = refresh_token_schema.load(request.json or {})
        
        # Refresh token
        success, tokens, error = AuthService.refresh_access_token(
            data['refresh_token']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'token_refresh_failed',
                'message': error
            }), 401
        
        return jsonify({
            'success': True,
            **tokens
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Invalid input data',
            'details': e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Token refresh failed'
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    User logout endpoint.
    
    Request Body (optional):
    {
        "refresh_token": "refresh_token_to_revoke"
    }
    
    Response:
    {
        "success": true,
        "message": "Logged out successfully"
    }
    """
    try:
        current_user = get_current_user()
        refresh_token = request.json.get('refresh_token') if request.json else None
        
        # Logout user
        success, error = AuthService.logout_user(
            user_id=current_user.id,
            refresh_token=refresh_token
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'logout_failed',
                'message': error
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Logout failed'
        }), 500

@auth_bp.route('/request-password-reset', methods=['POST'])
@limiter.limit("3 per hour")
def request_password_reset():
    """
    Request password reset endpoint.
    
    Request Body:
    {
        "email": "user@example.com"
    }
    
    Response:
    {
        "success": true,
        "message": "Password reset instructions sent to email"
    }
    """
    try:
        # Validate input
        data = password_reset_request_schema.load(request.json or {})
        
        # Request password reset
        success, token, user, error = AuthService.request_password_reset(
            email=data['email']
        )
        
        # Always return success for security (don't reveal if email exists)
        if success and token and user:
            # TODO: Send email with reset token
            # EmailService.send_password_reset_email(user.email, token)
            current_app.logger.info(f"Password reset requested for {user.email}")
        
        return jsonify({
            'success': True,
            'message': 'If the email exists, password reset instructions have been sent'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Invalid input data',
            'details': e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Password reset request error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Password reset request failed'
        }), 500

@auth_bp.route('/reset-password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password():
    """
    Reset password endpoint.
    
    Request Body:
    {
        "token": "reset_token",
        "new_password": "NewSecurePass123!"
    }
    
    Response:
    {
        "success": true,
        "message": "Password reset successfully"
    }
    """
    try:
        # Validate input
        data = password_reset_schema.load(request.json or {})
        
        # Reset password
        success, user, error = AuthService.reset_password(
            reset_token=data['token'],
            new_password=data['new_password']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'password_reset_failed',
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Invalid input data',
            'details': e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Password reset error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Password reset failed'
        }), 500

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user_info():
    """
    Get current user information.
    
    Response:
    {
        "success": true,
        "user": {...}
    }
    """
    try:
        current_user = get_current_user()
        
        if not current_user:
            return jsonify({
                'success': False,
                'error': 'user_not_found',
                'message': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get current user error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to get user information'
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@require_fresh_token()
def change_password():
    """
    Change password endpoint (requires fresh token).
    
    Request Body:
    {
        "current_password": "CurrentPass123!",
        "new_password": "NewSecurePass123!"
    }
    
    Response:
    {
        "success": true,
        "message": "Password changed successfully"
    }
    """
    try:
        current_user = get_current_user()
        
        # Validate input
        data = change_password_schema.load(request.json or {})
        
        # Change password
        success, error = AuthService.change_password(
            user=current_user,
            current_password=data['current_password'],
            new_password=data['new_password']
        )
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'password_change_failed',
                'message': error
            }), 400
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        }), 200
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'validation_error',
            'message': 'Invalid input data',
            'details': e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Password change error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Password change failed'
        }), 500

@auth_bp.route('/sessions', methods=['GET'])
@jwt_required()
def get_user_sessions():
    """
    Get user's active sessions.
    
    Response:
    {
        "success": true,
        "sessions": [...]
    }
    """
    try:
        current_user = get_current_user()
        sessions = AuthService.get_user_sessions(current_user.id)
        
        return jsonify({
            'success': True,
            'sessions': [session.to_dict() for session in sessions]
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Get sessions error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Failed to get sessions'
        }), 500

# Admin-only endpoints
@auth_bp.route('/admin/cleanup', methods=['POST'])
@require_role('admin')
def cleanup_tokens():
    """
    Admin endpoint to cleanup expired tokens.
    
    Response:
    {
        "success": true,
        "cleanup_stats": {...}
    }
    """
    try:
        stats = AuthService.cleanup_expired_tokens()
        
        return jsonify({
            'success': True,
            'cleanup_stats': stats
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Cleanup error: {e}")
        return jsonify({
            'success': False,
            'error': 'internal_error',
            'message': 'Cleanup failed'
        }), 500