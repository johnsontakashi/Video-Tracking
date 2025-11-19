from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_current_user, verify_jwt_in_request
from app.models.user import UserRole

def require_role(required_role):
    """
    Decorator to require specific user role.
    
    Args:
        required_role: String or UserRole enum (e.g., 'admin', UserRole.ADMIN)
    
    Returns:
        403 if user doesn't have sufficient permissions
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            
            if not current_user:
                return jsonify({
                    'error': 'user_not_found',
                    'message': 'User not found'
                }), 404
            
            if not current_user.is_active:
                return jsonify({
                    'error': 'account_deactivated',
                    'message': 'Account has been deactivated'
                }), 403
            
            # Convert string to UserRole enum if needed
            if isinstance(required_role, str):
                try:
                    role_enum = UserRole(required_role.lower())
                except ValueError:
                    return jsonify({
                        'error': 'invalid_role',
                        'message': f'Invalid role: {required_role}'
                    }), 500
            else:
                role_enum = required_role
            
            # Check if user has required role
            if not current_user.has_role(role_enum):
                return jsonify({
                    'error': 'insufficient_permissions',
                    'message': f'This operation requires {role_enum.value} role or higher'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_admin():
    """Shortcut decorator for admin-only access."""
    return require_role(UserRole.ADMIN)

def require_analyst():
    """Shortcut decorator for analyst-level access."""
    return require_role(UserRole.ANALYST)

def require_verified_email():
    """
    Decorator to require verified email address.
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            
            if not current_user:
                return jsonify({
                    'error': 'user_not_found',
                    'message': 'User not found'
                }), 404
            
            if not current_user.email_verified:
                return jsonify({
                    'error': 'email_not_verified',
                    'message': 'Email address must be verified to access this resource'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def require_fresh_token():
    """
    Decorator to require fresh JWT token for sensitive operations.
    """
    def decorator(f):
        @wraps(f)
        @jwt_required(fresh=True)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def optional_jwt():
    """
    Decorator for optional JWT authentication.
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                verify_jwt_in_request(optional=True)
            except Exception:
                # If JWT verification fails, continue without authentication
                pass
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_current_user_safe():
    """
    Safely get current user without raising exceptions.
    Returns None if no user is authenticated.
    """
    try:
        verify_jwt_in_request(optional=True)
        return get_current_user()
    except Exception:
        return None