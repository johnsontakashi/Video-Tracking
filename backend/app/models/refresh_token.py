import secrets
import hashlib
from datetime import datetime, timedelta
from app import db

class RefreshToken(db.Model):
    """Refresh token model for JWT token management."""
    
    __tablename__ = 'refresh_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False, nullable=False)
    device_info = db.Column(db.String(500))  # Browser, IP, etc.
    
    def __init__(self, user_id, expires_in_days=30, device_info=None):
        """Initialize refresh token with secure random token."""
        self.user_id = user_id
        self.token_hash = self._generate_token_hash()
        self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        self.device_info = device_info
        
    def _generate_token_hash(self):
        """Generate secure token hash."""
        # Generate cryptographically secure random token
        token = secrets.token_urlsafe(32)
        # Hash the token before storing
        return hashlib.sha256(token.encode()).hexdigest()
    
    @classmethod
    def create_token(cls, user_id, device_info=None):
        """Create new refresh token and return raw token."""
        # Generate raw token
        raw_token = secrets.token_urlsafe(32)
        
        # Create token record with hashed version
        token_record = cls(user_id=user_id, device_info=device_info)
        token_record.token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        db.session.add(token_record)
        db.session.commit()
        
        return raw_token, token_record
    
    @classmethod
    def verify_token(cls, raw_token):
        """Verify raw token and return token record if valid."""
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        
        token_record = cls.query.filter_by(
            token_hash=token_hash,
            is_revoked=False
        ).first()
        
        if not token_record:
            return None
            
        # Check if token is expired
        if token_record.expires_at < datetime.utcnow():
            token_record.revoke()
            return None
            
        return token_record
    
    def revoke(self):
        """Revoke the refresh token."""
        self.is_revoked = True
        db.session.commit()
    
    def is_valid(self):
        """Check if token is valid (not revoked and not expired)."""
        return (
            not self.is_revoked and 
            self.expires_at > datetime.utcnow()
        )
    
    @classmethod
    def revoke_all_user_tokens(cls, user_id):
        """Revoke all refresh tokens for a user."""
        cls.query.filter_by(user_id=user_id, is_revoked=False).update(
            {'is_revoked': True}
        )
        db.session.commit()
    
    @classmethod
    def cleanup_expired(cls):
        """Clean up expired tokens."""
        expired_tokens = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        for token in expired_tokens:
            db.session.delete(token)
        
        db.session.commit()
        return len(expired_tokens)
    
    def to_dict(self):
        """Convert token to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'is_revoked': self.is_revoked,
            'device_info': self.device_info
        }
    
    def __repr__(self):
        return f'<RefreshToken user_id={self.user_id}>'