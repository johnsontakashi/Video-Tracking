import secrets
import hashlib
from datetime import datetime, timedelta
from app import db

class PasswordResetToken(db.Model):
    """Password reset token model."""
    
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token_hash = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, user_id, expires_in_hours=1):
        """Initialize password reset token."""
        self.user_id = user_id
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    @classmethod
    def create_token(cls, user_id):
        """Create new password reset token and return raw token."""
        # Generate cryptographically secure token
        raw_token = secrets.token_urlsafe(32)
        
        # Revoke any existing unused tokens for this user
        cls.query.filter_by(user_id=user_id, used_at=None).update(
            {'used_at': datetime.utcnow()}
        )
        
        # Create new token record with hashed version
        token_record = cls(user_id=user_id)
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
            used_at=None
        ).first()
        
        if not token_record:
            return None
            
        # Check if token is expired
        if token_record.expires_at < datetime.utcnow():
            return None
            
        return token_record
    
    def mark_as_used(self):
        """Mark token as used."""
        self.used_at = datetime.utcnow()
        db.session.commit()
    
    def is_valid(self):
        """Check if token is valid (not used and not expired)."""
        return (
            self.used_at is None and 
            self.expires_at > datetime.utcnow()
        )
    
    @classmethod
    def cleanup_expired(cls):
        """Clean up expired or used tokens."""
        expired_tokens = cls.query.filter(
            db.or_(
                cls.expires_at < datetime.utcnow(),
                cls.used_at.isnot(None)
            )
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
            'used_at': self.used_at.isoformat() if self.used_at else None,
            'created_at': self.created_at.isoformat()
        }
    
    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id}>'