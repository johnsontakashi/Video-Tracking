import bcrypt
import secrets
import re
from email_validator import validate_email, EmailNotValidError
from flask import current_app

def hash_password(password):
    """Hash password using bcrypt."""
    rounds = current_app.config.get('BCRYPT_LOG_ROUNDS', 12)
    salt = bcrypt.gensalt(rounds=rounds)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, password_hash):
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except (ValueError, TypeError):
        return False

def generate_secure_token(length=32):
    """Generate cryptographically secure random token."""
    return secrets.token_urlsafe(length)

def validate_password_strength(password):
    """
    Validate password strength.
    Returns tuple (is_valid, errors)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if len(password) > 128:
        errors.append("Password must be less than 128 characters")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Check for common passwords (basic check)
    common_passwords = [
        'password', '123456', '123456789', 'qwerty', 'abc123',
        'password123', 'admin', 'letmein', 'welcome', 'monkey'
    ]
    
    if password.lower() in common_passwords:
        errors.append("Password is too common")
    
    return len(errors) == 0, errors

def validate_email_format(email):
    """
    Validate email format.
    Returns tuple (is_valid, normalized_email, error)
    """
    try:
        # Normalize email
        normalized = validate_email(email.strip())
        return True, normalized.email, None
    except EmailNotValidError as e:
        return False, None, str(e)

def sanitize_input(text, max_length=None):
    """Sanitize text input."""
    if not isinstance(text, str):
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Limit length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    return text

def validate_name(name, field_name="Name"):
    """
    Validate user name fields.
    Returns tuple (is_valid, sanitized_name, error)
    """
    if not name:
        return False, None, f"{field_name} is required"
    
    # Sanitize
    name = sanitize_input(name, 100)
    
    if len(name) < 1:
        return False, None, f"{field_name} is required"
    
    if len(name) > 100:
        return False, None, f"{field_name} must be less than 100 characters"
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, None, f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, name, None

def get_client_ip(request):
    """Get client IP address from request."""
    # Check for forwarded headers (behind proxy)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def get_user_agent(request):
    """Get user agent from request."""
    return request.headers.get('User-Agent', '')[:500]  # Limit length