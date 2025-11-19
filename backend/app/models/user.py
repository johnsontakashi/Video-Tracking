import enum
from datetime import datetime
from app import db
from app.utils.security import hash_password, verify_password

class UserRole(enum.Enum):
    """User role enumeration."""
    GUEST = "guest"
    ANALYST = "analyst"
    ADMIN = "admin"
    
    @classmethod
    def get_hierarchy(cls):
        """Return role hierarchy (higher value = more permissions)."""
        return {
            cls.GUEST: 1,
            cls.ANALYST: 2,
            cls.ADMIN: 3
        }
    
    def has_permission(self, required_role):
        """Check if current role has permission for required role."""
        hierarchy = self.get_hierarchy()
        return hierarchy[self] >= hierarchy[required_role]

class User(db.Model):
    """User model with comprehensive authentication features."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.GUEST)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    refresh_tokens = db.relationship('RefreshToken', backref='user', cascade='all, delete-orphan')
    password_reset_tokens = db.relationship('PasswordResetToken', backref='user', cascade='all, delete-orphan')
    sessions = db.relationship('UserSession', backref='user', cascade='all, delete-orphan')
    
    def __init__(self, email, password, first_name, last_name, role=UserRole.GUEST):
        """Initialize user with hashed password."""
        self.email = email.lower().strip()
        self.password_hash = hash_password(password)
        self.first_name = first_name.strip()
        self.last_name = last_name.strip()
        self.role = role
    
    def set_password(self, password):
        """Set new password with proper hashing."""
        self.password_hash = hash_password(password)
        self.updated_at = datetime.utcnow()
    
    def verify_password(self, password):
        """Verify password against hash."""
        return verify_password(password, self.password_hash)
    
    def update_last_login(self):
        """Update last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def has_role(self, required_role):
        """Check if user has required role or higher."""
        if isinstance(required_role, str):
            required_role = UserRole(required_role)
        return self.role.has_permission(required_role)
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == UserRole.ADMIN
    
    def is_analyst(self):
        """Check if user is analyst or higher."""
        return self.has_role(UserRole.ANALYST)
    
    @property
    def full_name(self):
        """Return full name."""
        return f"{self.first_name} {self.last_name}"
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary."""
        data = {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'role': self.role.value,
            'is_active': self.is_active,
            'email_verified': self.email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    def __repr__(self):
        return f'<User {self.email}>'