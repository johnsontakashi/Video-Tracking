# 🎥 Video Tracking Project

A comprehensive full-stack application with authentication, role-based access control, and beautiful UI.

## 🏗️ Architecture

- **Frontend**: React with TypeScript + Context API
- **Backend**: Flask (Python) with JWT authentication
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Task Queue**: Celery
- **Message Broker**: Redis
- **Containerization**: Docker & Docker Compose

## ✨ Features

### 🔐 Authentication System
- **JWT-based authentication** with access + refresh tokens
- **Role-based access control** (Admin, Analyst, Guest)
- **Password reset flow** with secure tokens
- **Beautiful login/signup UI** with validation
- **Rate limiting** and security features

### 🎯 Core Features
- **User management** with comprehensive profiles
- **Protected routes** based on user roles
- **Real-time dashboard** with role-specific content
- **Asynchronous task processing** with Celery
- **RESTful API** with comprehensive documentation

## Quick Start

### With Docker (Recommended)

```bash
# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3001
# Backend: http://localhost:5001
```

### Manual Setup

#### 1. Database Setup (PostgreSQL)
```bash
# Install PostgreSQL and create database
createdb video_tracking_db
psql video_tracking_db -c "CREATE USER video_user WITH PASSWORD 'secure_password';"
psql video_tracking_db -c "GRANT ALL PRIVILEGES ON DATABASE video_tracking_db TO video_user;"
```

#### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database with sample users
python run.py init-db

# Start the application
python run.py
```

#### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### 4. Additional Services (Optional)
```bash
# Start Redis for Celery (if using async tasks)
redis-server

# Start Celery worker (in another terminal)
cd backend
celery -A app.celery worker --loglevel=info
```

## 📚 Documentation

- **[Complete Authentication Guide](AUTH_DOCUMENTATION.md)** - Detailed implementation guide
- **API Documentation** - Available at `/api/auth/` endpoints
- **Database Schema** - ERD diagram in documentation

## 🔌 API Endpoints

### Authentication
- `POST /api/auth/signup` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/request-password-reset` - Request password reset
- `POST /api/auth/reset-password` - Reset password
- `GET /api/auth/me` - Get current user info

### Protected Routes
- `GET /api/guest-area` - All authenticated users
- `GET /api/analyst-area` - Analysts and admins only
- `GET /api/admin-area` - Admins only

## 🏗️ Project Structure

```
├── backend/
│   ├── app/
│   │   ├── models/         # Database models
│   │   ├── routes/         # API routes
│   │   ├── services/       # Business logic
│   │   ├── middleware/     # Auth middleware
│   │   └── utils/          # Utility functions
│   ├── run.py             # Application entry point
│   ├── config.py          # Configuration
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts
│   │   ├── services/      # API services
│   │   └── utils/         # Utility functions
│   └── package.json       # Node dependencies
├── docker-compose.yml     # Multi-service orchestration
├── AUTH_DOCUMENTATION.md  # Complete auth guide
└── README.md             # This file
```

## 👥 Sample Users

After running `python run.py init-db`, you can login with:

- **Admin**: admin@videotracking.com / AdminPass123!
- **Analyst**: analyst@videotracking.com / AnalystPass123!
- **Guest**: guest@videotracking.com / GuestPass123!

## Development Notes

- Frontend runs on port 3001
- Backend runs on port 5001
- Redis runs on port 6379
- CORS is configured for localhost:3001
- All services auto-reload on file changes in development mode