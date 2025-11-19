# 🔐 Video Tracking Authentication System

A comprehensive authentication system with JWT tokens, role-based access control, and beautiful UI.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Database Schema](#database-schema)
- [API Endpoints](#api-endpoints)
- [Security Features](#security-features)
- [Frontend Implementation](#frontend-implementation)
- [Setup Instructions](#setup-instructions)
- [Usage Examples](#usage-examples)

## 🏗️ Architecture Overview

### Technology Stack

- **Backend**: Flask (Python) with JWT authentication
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Frontend**: React (TypeScript) with Context API
- **Tokens**: JWT access tokens + secure refresh tokens
- **Security**: bcrypt password hashing, rate limiting
- **Validation**: Marshmallow schemas with comprehensive validation

### Authentication Flow

1. **User Registration** → Email/password validation → Secure storage
2. **User Login** → Credentials verification → JWT tokens generation
3. **Token Usage** → Access token in Authorization header → Automatic refresh
4. **Role Authorization** → Middleware checks user permissions → Route protection

## 📊 Database Schema

```ascii
┌─────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│     Users       │    │   RefreshTokens      │    │ PasswordResetTokens │
├─────────────────┤    ├──────────────────────┤    ├─────────────────────┤
│ id (PK)         │◄──┤ user_id (FK)         │    │ id (PK)             │
│ email (UNIQUE)  │    │ token_hash           │    │ user_id (FK)        │──┐
│ password_hash   │    │ expires_at           │    │ token_hash          │  │
│ first_name      │    │ created_at           │    │ expires_at          │  │
│ last_name       │    │ is_revoked           │    │ used_at             │  │
│ role            │    │ device_info          │    │ created_at          │  │
│ is_active       │    └──────────────────────┘    └─────────────────────┘  │
│ email_verified  │                                                        │
│ last_login      │                                ┌─────────────────────┐  │
│ created_at      │                                │     UserSessions    │  │
│ updated_at      │                                ├─────────────────────┤  │
└─────────────────┘                                │ id (PK)             │  │
                                                   │ user_id (FK)        │──┘
    ENUM: role                                     │ session_token       │
    - admin (level 3)                              │ ip_address          │
    - analyst (level 2)                            │ user_agent          │
    - guest (level 1)                              │ expires_at          │
                                                   │ created_at          │
                                                   │ last_activity       │
                                                   └─────────────────────┘
```

## 🔌 API Endpoints

### Authentication Endpoints

#### POST `/api/auth/signup`
**Register new user**

```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "guest"
}

// Response (201)
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "guest",
    "created_at": "2024-01-01T00:00:00"
  }
}

// Error (400)
{
  "success": false,
  "error": "validation_error",
  "details": {
    "password": ["Password must contain at least one uppercase letter"]
  }
}
```

#### POST `/api/auth/login`
**Authenticate user**

```json
// Request
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "remember_me": false
}

// Response (200)
{
  "success": true,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "secure_random_token_here",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {...}
}
```

#### POST `/api/auth/refresh`
**Refresh access token**

```json
// Request
{
  "refresh_token": "secure_random_token_here"
}

// Response (200)
{
  "success": true,
  "access_token": "new_jwt_token_here",
  "token_type": "Bearer",
  "expires_in": 900,
  "user": {...}
}
```

#### POST `/api/auth/logout`
**Logout user**

```json
// Request (optional)
{
  "refresh_token": "token_to_revoke"
}

// Response (200)
{
  "success": true,
  "message": "Logged out successfully"
}
```

#### POST `/api/auth/request-password-reset`
**Request password reset**

```json
// Request
{
  "email": "user@example.com"
}

// Response (200) - Always success for security
{
  "success": true,
  "message": "If the email exists, password reset instructions have been sent"
}
```

#### POST `/api/auth/reset-password`
**Reset password with token**

```json
// Request
{
  "token": "reset_token_from_email",
  "new_password": "NewSecurePass123!"
}

// Response (200)
{
  "success": true,
  "message": "Password reset successfully"
}
```

#### GET `/api/auth/me`
**Get current user info** (Requires Authentication)

```json
// Response (200)
{
  "success": true,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "guest",
    "is_active": true,
    "email_verified": false,
    "last_login": "2024-01-01T00:00:00",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

### Protected Endpoints Examples

#### GET `/api/guest-area`
**Accessible to all authenticated users**

#### GET `/api/analyst-area`
**Accessible to analysts and admins only**

#### GET `/api/admin-area`
**Accessible to admins only**

## 🔒 Security Features

### 1. JWT-based Authentication

**Why JWT?**
- Stateless authentication
- Scalable across multiple servers
- Built-in expiration
- Secure token verification

**Access Tokens**: Short-lived (15 minutes), contain user claims
**Refresh Tokens**: Long-lived (30 days), stored securely, can be revoked

### 2. Password Security

```python
# bcrypt with configurable rounds
BCRYPT_LOG_ROUNDS = 12  # Adjustable based on security needs

# Password strength requirements:
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character
- Not in common passwords list
```

### 3. Role-based Access Control

```python
# Role hierarchy (higher value = more permissions)
GUEST = 1     # Basic access
ANALYST = 2   # Data analysis features
ADMIN = 3     # Full system access

# Usage example
@require_role('analyst')
def analyst_endpoint():
    # Only accessible to analysts and admins
    pass

@require_admin()
def admin_endpoint():
    # Only accessible to admins
    pass
```

### 4. Rate Limiting

```python
# API endpoint limits
@limiter.limit("5 per minute")   # Signup
@limiter.limit("10 per minute")  # Login
@limiter.limit("3 per hour")     # Password reset
@limiter.limit("20 per minute")  # Token refresh
```

### 5. Input Validation

```python
# Email validation with normalization
# Password strength checking
# SQL injection prevention
# XSS protection
# CSRF protection with proper headers
```

## 💻 Frontend Implementation

### Token Management Strategy

**Storage**: localStorage with HttpOnly cookie fallback
**Auto-refresh**: Automatic token renewal before expiration
**Error handling**: Graceful authentication failure handling

### React Context Pattern

```typescript
const { user, login, logout, hasRole, isAdmin } = useAuth();

// Usage in components
if (hasRole('analyst')) {
  // Show analyst features
}

if (isAdmin()) {
  // Show admin controls
}
```

### Beautiful UI Components

- **Responsive design** with mobile-first approach
- **Beautiful gradients** and smooth animations
- **Form validation** with real-time feedback
- **Loading states** with elegant spinners
- **Error handling** with user-friendly messages

### Frontend Login Example

```typescript
// Login function
const handleLogin = async (email: string, password: string) => {
  try {
    const response = await authService.login(email, password);
    // Token automatically stored and user updated
  } catch (error) {
    // Show error message to user
  }
};

// API requests with automatic token attachment
const apiRequest = async (url: string, options: RequestInit = {}) => {
  const token = authService.getAccessToken();
  
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
};
```

## 🚀 Setup Instructions

### Backend Setup

```bash
# 1. Create virtual environment
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 4. Set up PostgreSQL database
# Install PostgreSQL and create database:
createdb video_tracking_db

# 5. Initialize database
python run.py init-db

# 6. Run the application
python run.py
```

### Frontend Setup

```bash
# 1. Install dependencies
cd frontend
npm install

# 2. Set up environment variables
cp .env.example .env
# Edit REACT_APP_API_URL if needed

# 3. Start development server
npm start
```

### Database Setup

```sql
-- PostgreSQL setup
CREATE DATABASE video_tracking_db;
CREATE USER video_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE video_tracking_db TO video_user;
```

### Environment Variables

**Backend (.env)**:
```env
DATABASE_URL=postgresql://video_user:secure_password@localhost:5432/video_tracking_db
JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRES=15
JWT_REFRESH_TOKEN_EXPIRES=30
REDIS_URL=redis://localhost:6379/0
BCRYPT_LOG_ROUNDS=12
```

**Frontend (.env)**:
```env
REACT_APP_API_URL=http://localhost:5001
```

## 📖 Usage Examples

### Backend Role Protection

```python
from app.middleware.auth import require_role, require_admin

@app.route('/api/sensitive-data')
@require_role('analyst')  # Requires analyst or higher
def get_sensitive_data():
    current_user = get_current_user()
    return jsonify({'data': 'sensitive information'})

@app.route('/api/admin/users')
@require_admin()  # Requires admin role
def manage_users():
    # Admin-only functionality
    pass
```

### Frontend Route Protection

```typescript
// Protected component
const ProtectedRoute: React.FC<{children: ReactNode, requiredRole?: string}> = 
  ({ children, requiredRole }) => {
  const { isAuthenticated, hasRole } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  if (requiredRole && !hasRole(requiredRole)) {
    return <div>Access Denied</div>;
  }
  
  return <>{children}</>;
};

// Usage
<ProtectedRoute requiredRole="admin">
  <AdminPanel />
</ProtectedRoute>
```

### Sample Users

The system includes sample users for testing:

- **Admin**: admin@videotracking.com / AdminPass123!
- **Analyst**: analyst@videotracking.com / AnalystPass123!
- **Guest**: guest@videotracking.com / GuestPass123!

## 🎯 Key Benefits

1. **Security First**: Industry-standard authentication with JWT
2. **Beautiful UI**: Modern, responsive design with smooth animations
3. **Role-based Access**: Granular permission control
4. **Optimized Code**: Clean architecture with separation of concerns
5. **PostgreSQL Ready**: Robust database schema with relationships
6. **Production Ready**: Rate limiting, validation, and error handling
7. **Developer Friendly**: Comprehensive documentation and examples

## 🔧 Customization

The system is highly configurable:

- **Token expiration times** can be adjusted
- **Password policies** can be modified
- **Rate limits** can be customized
- **New roles** can be easily added
- **UI themes** can be changed

This authentication system provides a solid foundation for any application requiring secure user management with role-based access control.