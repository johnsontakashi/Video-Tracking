from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_current_user
from app.middleware.auth import require_role, require_admin, require_analyst, optional_jwt, get_current_user_safe

main_bp = Blueprint('main', __name__)

@main_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Video Tracking API is running'
    }), 200

@main_bp.route('/hello', methods=['GET'])
@optional_jwt()
def hello():
    """
    Hello endpoint with optional authentication.
    Returns different message based on authentication status.
    """
    current_user = get_current_user_safe()
    
    if current_user:
        return jsonify({
            'message': f'Hello {current_user.full_name}! Welcome back to Video Tracking.',
            'authenticated': True,
            'user': current_user.to_dict()
        }), 200
    else:
        return jsonify({
            'message': 'Hello! Welcome to Video Tracking API.',
            'authenticated': False
        }), 200

# Protected endpoints for different roles
@main_bp.route('/guest-area', methods=['GET'])
@jwt_required()
def guest_area():
    """Endpoint accessible to all authenticated users."""
    current_user = get_current_user()
    
    return jsonify({
        'message': f'Welcome to the guest area, {current_user.full_name}!',
        'user_role': current_user.role.value
    }), 200

@main_bp.route('/analyst-area', methods=['GET'])
@require_analyst()
def analyst_area():
    """Endpoint accessible to analysts and admins only."""
    current_user = get_current_user()
    
    return jsonify({
        'message': f'Welcome to the analyst area, {current_user.full_name}!',
        'user_role': current_user.role.value,
        'access_level': 'analyst'
    }), 200

@main_bp.route('/admin-area', methods=['GET'])
@require_admin()
def admin_area():
    """Endpoint accessible to admins only."""
    current_user = get_current_user()
    
    return jsonify({
        'message': f'Welcome to the admin area, {current_user.full_name}!',
        'user_role': current_user.role.value,
        'access_level': 'admin'
    }), 200

@main_bp.route('/demo/role-test/<role>', methods=['GET'])
@jwt_required()
def test_role_access(role):
    """
    Demo endpoint to test role-based access.
    Usage: GET /api/demo/role-test/admin
    """
    current_user = get_current_user()
    
    try:
        required_role = role.lower()
        has_access = current_user.has_role(required_role)
        
        return jsonify({
            'message': f'Role access test for: {required_role}',
            'user_role': current_user.role.value,
            'has_access': has_access,
            'test_result': 'PASS' if has_access else 'FAIL'
        }), 200
        
    except ValueError:
        return jsonify({
            'error': 'invalid_role',
            'message': f'Invalid role: {role}',
            'valid_roles': ['guest', 'analyst', 'admin']
        }), 400

# Error handlers
@main_bp.errorhandler(403)
def forbidden(error):
    """Handle 403 Forbidden errors."""
    return jsonify({
        'error': 'forbidden',
        'message': 'You do not have permission to access this resource'
    }), 403

@main_bp.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors."""
    return jsonify({
        'error': 'not_found',
        'message': 'The requested resource was not found'
    }), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server errors."""
    return jsonify({
        'error': 'internal_error',
        'message': 'An internal server error occurred'
    }), 500