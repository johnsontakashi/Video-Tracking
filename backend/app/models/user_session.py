import secrets
from datetime import datetime, timedelta
from app import db

class UserSession(db.Model):
    """User session model for tracking active sessions."""
    
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(255), nullable=False, unique=True, index=True)
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(500))
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, user_id, ip_address=None, user_agent=None, expires_in_days=7):
        """Initialize user session."""
        self.user_id = user_id
        self.session_token = secrets.token_urlsafe(32)
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    def is_valid(self):
        """Check if session is valid (not expired)."""
        return self.expires_at > datetime.utcnow()
    
    def extend_session(self, days=7):
        """Extend session expiry."""
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.last_activity = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_active_sessions(cls, user_id):
        """Get all active sessions for a user."""
        return cls.query.filter_by(user_id=user_id).filter(
            cls.expires_at > datetime.utcnow()
        ).order_by(cls.last_activity.desc()).all()
    
    @classmethod
    def cleanup_expired(cls):
        """Clean up expired sessions."""
        expired_sessions = cls.query.filter(
            cls.expires_at < datetime.utcnow()
        ).all()
        
        for session in expired_sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(expired_sessions)
    
    @classmethod
    def revoke_all_user_sessions(cls, user_id, except_session_id=None):
        """Revoke all sessions for a user except optionally one."""
        query = cls.query.filter_by(user_id=user_id)
        
        if except_session_id:
            query = query.filter(cls.id != except_session_id)
        
        sessions = query.all()
        for session in sessions:
            db.session.delete(session)
        
        db.session.commit()
        return len(sessions)
    
    def to_dict(self, include_token=False):
        """Convert session to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'expires_at': self.expires_at.isoformat(),
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat()
        }
        
        if include_token:
            data['session_token'] = self.session_token
            
        return data
    
    def __repr__(self):
        return f'<UserSession user_id={self.user_id}, ip={self.ip_address}>'