from marshmallow import Schema, fields, validate, post_load, ValidationError
from app.utils.security import validate_password_strength, validate_email_format, validate_name

class SignupSchema(Schema):
    """Schema for user signup validation."""
    
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    role = fields.Str(missing='guest', validate=validate.OneOf(['guest', 'analyst', 'admin']))
    
    @post_load
    def validate_data(self, data, **kwargs):
        """Custom validation after loading."""
        errors = {}
        
        # Validate email format
        is_valid_email, normalized_email, email_error = validate_email_format(data['email'])
        if not is_valid_email:
            errors['email'] = email_error
        else:
            data['email'] = normalized_email
        
        # Validate password strength
        is_strong_password, password_errors = validate_password_strength(data['password'])
        if not is_strong_password:
            errors['password'] = password_errors
        
        # Validate first name
        is_valid_first, first_name, first_error = validate_name(data['first_name'], 'First name')
        if not is_valid_first:
            errors['first_name'] = first_error
        else:
            data['first_name'] = first_name
        
        # Validate last name
        is_valid_last, last_name, last_error = validate_name(data['last_name'], 'Last name')
        if not is_valid_last:
            errors['last_name'] = last_error
        else:
            data['last_name'] = last_name
        
        if errors:
            raise ValidationError(errors)
        
        return data

class LoginSchema(Schema):
    """Schema for user login validation."""
    
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })
    password = fields.Str(required=True, error_messages={
        'required': 'Password is required'
    })
    remember_me = fields.Bool(missing=False)
    
    @post_load
    def validate_data(self, data, **kwargs):
        """Custom validation after loading."""
        # Normalize email
        is_valid_email, normalized_email, email_error = validate_email_format(data['email'])
        if not is_valid_email:
            raise ValidationError({'email': email_error})
        
        data['email'] = normalized_email
        return data

class PasswordResetRequestSchema(Schema):
    """Schema for password reset request validation."""
    
    email = fields.Email(required=True, error_messages={
        'required': 'Email is required',
        'invalid': 'Invalid email format'
    })
    
    @post_load
    def validate_data(self, data, **kwargs):
        """Custom validation after loading."""
        # Normalize email
        is_valid_email, normalized_email, email_error = validate_email_format(data['email'])
        if not is_valid_email:
            raise ValidationError({'email': email_error})
        
        data['email'] = normalized_email
        return data

class PasswordResetSchema(Schema):
    """Schema for password reset validation."""
    
    token = fields.Str(required=True, error_messages={
        'required': 'Reset token is required'
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    
    @post_load
    def validate_data(self, data, **kwargs):
        """Custom validation after loading."""
        # Validate password strength
        is_strong_password, password_errors = validate_password_strength(data['new_password'])
        if not is_strong_password:
            raise ValidationError({'new_password': password_errors})
        
        return data

class ChangePasswordSchema(Schema):
    """Schema for password change validation."""
    
    current_password = fields.Str(required=True, error_messages={
        'required': 'Current password is required'
    })
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    
    @post_load
    def validate_data(self, data, **kwargs):
        """Custom validation after loading."""
        # Validate password strength
        is_strong_password, password_errors = validate_password_strength(data['new_password'])
        if not is_strong_password:
            raise ValidationError({'new_password': password_errors})
        
        # Check if passwords are different
        if data['current_password'] == data['new_password']:
            raise ValidationError({'new_password': 'New password must be different from current password'})
        
        return data

class RefreshTokenSchema(Schema):
    """Schema for refresh token validation."""
    
    refresh_token = fields.Str(required=True, error_messages={
        'required': 'Refresh token is required'
    })