from datetime import datetime, timedelta
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity
from sqlalchemy.exc import IntegrityError

from app import db
from app.models.user import User, UserRole
from app.models.refresh_token import RefreshToken
from app.models.password_reset_token import PasswordResetToken
from app.models.user_session import UserSession
from app.utils.security import get_client_ip, get_user_agent

class AuthService:
    """Service class for authentication operations."""
    
    @staticmethod
    def register_user(email, password, first_name, last_name, role=UserRole.GUEST):
        """
        Register a new user.
        
        Returns:
            tuple: (success: bool, user: User|None, error: str|None)
        """
        try:
            # Check if user already exists
            if User.query.filter_by(email=email.lower()).first():
                return False, None, "User with this email already exists"
            
            # Create new user
            user = User(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role=role
            )
            
            db.session.add(user)
            db.session.commit()
            
            return True, user, None
            
        except IntegrityError:
            db.session.rollback()
            return False, None, "User with this email already exists"
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering user: {e}")
            return False, None, "Registration failed"
    
    @staticmethod
    def authenticate_user(email, password, request=None):
        """
        Authenticate user with email and password.
        
        Returns:
            tuple: (success: bool, user: User|None, tokens: dict|None, error: str|None)
        """
        try:
            # Find user
            user = User.query.filter_by(email=email.lower()).first()
            
            if not user:
                return False, None, None, "Invalid email or password"
            
            # Check if account is active
            if not user.is_active:
                return False, None, None, "Account has been deactivated"
            
            # Verify password
            if not user.verify_password(password):
                return False, None, None, "Invalid email or password"
            
            # Update last login
            user.update_last_login()
            
            # Generate tokens
            tokens = AuthService.generate_tokens(user, request)
            
            return True, user, tokens, None
            
        except Exception as e:
            current_app.logger.error(f"Error authenticating user: {e}")
            return False, None, None, "Authentication failed"
    
    @staticmethod
    def generate_tokens(user, request=None, remember_me=False):
        """
        Generate JWT access and refresh tokens for user.
        
        Returns:
            dict: Contains access_token, refresh_token, and metadata
        """
        # Get device info if request is provided
        device_info = None
        if request:
            ip_address = get_client_ip(request)
            user_agent = get_user_agent(request)
            device_info = f"IP: {ip_address}, Agent: {user_agent}"
        
        # Create access token
        access_token = create_access_token(
            identity=user.id,
            fresh=True  # Mark as fresh token
        )
        
        # Create refresh token with extended expiry if remember_me
        expires_in_days = 30 if remember_me else 7
        raw_refresh_token, refresh_token_record = RefreshToken.create_token(
            user_id=user.id,
            device_info=device_info
        )
        
        # Create user session
        if request:
            session = UserSession(
                user_id=user.id,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                expires_in_days=expires_in_days
            )
            db.session.add(session)
            db.session.commit()
        
        return {
            'access_token': access_token,
            'refresh_token': raw_refresh_token,
            'token_type': 'Bearer',
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds(),
            'user': user.to_dict()
        }
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """
        Generate new access token using refresh token.
        
        Returns:
            tuple: (success: bool, tokens: dict|None, error: str|None)
        """
        try:
            # Verify refresh token
            token_record = RefreshToken.verify_token(refresh_token)
            
            if not token_record:
                return False, None, "Invalid or expired refresh token"
            
            # Get user
            user = User.query.get(token_record.user_id)
            
            if not user or not user.is_active:
                return False, None, "User not found or inactive"
            
            # Create new access token
            access_token = create_access_token(
                identity=user.id,
                fresh=False  # Refreshed tokens are not fresh
            )
            
            return True, {
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds(),
                'user': user.to_dict()
            }, None
            
        except Exception as e:
            current_app.logger.error(f"Error refreshing token: {e}")
            return False, None, "Token refresh failed"
    
    @staticmethod
    def revoke_refresh_token(refresh_token):
        """
        Revoke a refresh token.
        
        Returns:
            tuple: (success: bool, error: str|None)
        """
        try:
            token_record = RefreshToken.verify_token(refresh_token)
            
            if token_record:
                token_record.revoke()
                return True, None
            
            return False, "Token not found"
            
        except Exception as e:
            current_app.logger.error(f"Error revoking token: {e}")
            return False, "Token revocation failed"
    
    @staticmethod
    def logout_user(user_id, refresh_token=None):
        """
        Logout user by revoking tokens and sessions.
        
        Returns:
            tuple: (success: bool, error: str|None)
        """
        try:
            if refresh_token:
                # Revoke specific refresh token
                AuthService.revoke_refresh_token(refresh_token)
            else:
                # Revoke all refresh tokens for user
                RefreshToken.revoke_all_user_tokens(user_id)
            
            # Revoke all user sessions
            UserSession.revoke_all_user_sessions(user_id)
            
            return True, None
            
        except Exception as e:
            current_app.logger.error(f"Error logging out user: {e}")
            return False, "Logout failed"
    
    @staticmethod
    def request_password_reset(email):
        """
        Create password reset token for user.
        
        Returns:
            tuple: (success: bool, token: str|None, user: User|None, error: str|None)
        """
        try:
            # Find user
            user = User.query.filter_by(email=email.lower()).first()
            
            if not user:
                # Don't reveal if email exists or not
                return True, None, None, None
            
            if not user.is_active:
                return False, None, None, "Account has been deactivated"
            
            # Create reset token
            raw_token, token_record = PasswordResetToken.create_token(user.id)
            
            return True, raw_token, user, None
            
        except Exception as e:
            current_app.logger.error(f"Error requesting password reset: {e}")
            return False, None, None, "Password reset request failed"
    
    @staticmethod
    def reset_password(reset_token, new_password):
        """
        Reset password using reset token.
        
        Returns:
            tuple: (success: bool, user: User|None, error: str|None)
        """
        try:
            # Verify reset token
            token_record = PasswordResetToken.verify_token(reset_token)
            
            if not token_record:
                return False, None, "Invalid or expired reset token"
            
            # Get user
            user = User.query.get(token_record.user_id)
            
            if not user or not user.is_active:
                return False, None, "User not found or inactive"
            
            # Update password
            user.set_password(new_password)
            
            # Mark token as used
            token_record.mark_as_used()
            
            # Revoke all existing refresh tokens for security
            RefreshToken.revoke_all_user_tokens(user.id)
            
            # Revoke all existing sessions
            UserSession.revoke_all_user_sessions(user.id)
            
            db.session.commit()
            
            return True, user, None
            
        except Exception as e:
            current_app.logger.error(f"Error resetting password: {e}")
            db.session.rollback()
            return False, None, "Password reset failed"
    
    @staticmethod
    def change_password(user, current_password, new_password):
        """
        Change password for authenticated user.
        
        Returns:
            tuple: (success: bool, error: str|None)
        """
        try:
            # Verify current password
            if not user.verify_password(current_password):
                return False, "Current password is incorrect"
            
            # Update password
            user.set_password(new_password)
            
            # Revoke all existing refresh tokens except current session
            RefreshToken.revoke_all_user_tokens(user.id)
            
            db.session.commit()
            
            return True, None
            
        except Exception as e:
            current_app.logger.error(f"Error changing password: {e}")
            db.session.rollback()
            return False, "Password change failed"
    
    @staticmethod
    def get_user_sessions(user_id):
        """
        Get active sessions for user.
        
        Returns:
            list: List of active sessions
        """
        return UserSession.get_active_sessions(user_id)
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        Clean up expired tokens and sessions.
        
        Returns:
            dict: Cleanup statistics
        """
        try:
            refresh_count = RefreshToken.cleanup_expired()
            reset_count = PasswordResetToken.cleanup_expired()
            session_count = UserSession.cleanup_expired()
            
            return {
                'refresh_tokens_cleaned': refresh_count,
                'reset_tokens_cleaned': reset_count,
                'sessions_cleaned': session_count
            }
            
        except Exception as e:
            current_app.logger.error(f"Error cleaning up tokens: {e}")
            return {
                'error': 'Cleanup failed'
            }