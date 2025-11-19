from flask_jwt_extended import get_jwt, get_jwt_identity
from app.models.refresh_token import RefreshToken
from app.models.user import User

def configure_jwt_handlers(jwt, db):
    """Configure JWT handlers for token management."""
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """Check if JWT token is revoked."""
        jti = jwt_payload['jti']  # JWT ID
        token_type = jwt_payload['type']
        
        if token_type == 'refresh':
            # For refresh tokens, check if it exists in database and is not revoked
            token_record = RefreshToken.verify_token(jti)
            return token_record is None
        
        # For access tokens, we could implement a blocklist in Redis
        # For now, we'll rely on short expiration times
        return False
    
    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """Define how to get user identity from user object."""
        if isinstance(user, User):
            return user.id
        return user
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """Load user from JWT token."""
        identity = jwt_data["sub"]
        return User.query.get(identity)
    
    @jwt.additional_claims_loader
    def add_claims_to_jwt(identity):
        """Add additional claims to JWT token."""
        user = User.query.get(identity)
        if user:
            return {
                'role': user.role.value,
                'email': user.email,
                'email_verified': user.email_verified
            }
        return {}
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        """Handle expired token."""
        return {
            'error': 'token_expired',
            'message': 'The token has expired'
        }, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        """Handle invalid token."""
        return {
            'error': 'invalid_token',
            'message': 'Token is invalid'
        }, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        """Handle missing token."""
        return {
            'error': 'missing_token',
            'message': 'Authorization token is required'
        }, 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        """Handle revoked token."""
        return {
            'error': 'token_revoked',
            'message': 'The token has been revoked'
        }, 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        """Handle non-fresh token when fresh token is required."""
        return {
            'error': 'fresh_token_required',
            'message': 'Fresh token is required for this operation'
        }, 401