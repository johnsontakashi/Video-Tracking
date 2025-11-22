# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Influencer Analytics Platform** - a comprehensive social media analytics system for tracking and analyzing influencer profiles across Instagram, YouTube, TikTok, and Twitter. The platform features user management, analytics dashboards, and role-based access control.

**🚀 RECENTLY REFACTORED (Nov 2025)**: The codebase has been cleaned up and simplified for better maintainability.

## Architecture

**Current Stack**: Flask (Python) + React (TypeScript) + SQLite (development)
- **Backend**: Simplified Flask API (backend/app.py) with SQLite database, token authentication
- **Frontend**: React with TypeScript, Ant Design UI components, responsive dashboards  
- **Database**: SQLite with automatic initialization (politikos_full.db)
- **Authentication**: Simple token-based authentication
- **File Structure**: Clean structure with complex legacy code moved to backup_old_servers/

**Production Stack** (Docker Compose): Flask + React + PostgreSQL + Redis + Celery
- **Database**: PostgreSQL with Redis for caching and task queues
- **Background Tasks**: Celery workers with Flower monitoring
- **Deployment**: Containerized with automated deployment scripts

## Development Commands

### Local Development Setup

**Backend (Python/Flask)**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py  # Starts on port 5000
```

**Frontend (React/TypeScript)**:
```bash
cd frontend
npm install
npm start      # Development server on port 3000
npm run build  # Production build
npm test       # Run tests
```

**Database**: SQLite database (politikos_full.db) is automatically created when running backend/app.py

### Production Deployment

```bash
# Deploy entire containerized stack
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Database backup
./scripts/backup.sh --full

# Container management
docker-compose up -d         # Start all services
docker-compose ps            # Check service status  
docker-compose logs backend  # View specific service logs
docker-compose restart      # Restart services
```

## Key Directory Structure

```
├── backend/                 # Flask API server
│   ├── app.py              # Main simplified Flask application (SQLite-based)
│   ├── app/                # Feature modules (complex architecture for production)
│   │   ├── models/         # Database models (User, Influencer, Analytics, etc.)
│   │   ├── services/       # Business logic and API services
│   │   ├── collectors/     # Social media data collection modules
│   │   ├── routes/         # API route definitions
│   │   ├── tasks/          # Celery background tasks
│   │   ├── utils/          # Authentication and utility functions
│   │   └── middleware/     # Authentication middleware
│   ├── backup_old_servers/ # Legacy complex implementations
│   └── requirements.txt    # Python dependencies
├── frontend/               # React TypeScript application
│   ├── src/
│   │   ├── components/     # Feature-organized React components
│   │   │   ├── Analytics/  # Analytics dashboard components
│   │   │   ├── Auth/       # Login/signup components
│   │   │   ├── Dashboard/  # Main dashboard components
│   │   │   ├── Influencers/ # Influencer management
│   │   │   └── Navigation/ # Navigation components
│   │   ├── services/       # API service functions
│   │   ├── contexts/       # React Context providers (Auth, etc.)
│   │   └── utils/          # Frontend utility functions
│   └── package.json        # Node.js dependencies
├── scripts/                # Deployment and maintenance scripts
│   ├── deploy.sh          # Production deployment script
│   └── backup.sh          # Database backup script
└── docker-compose.yml     # Container orchestration for production
```

## Current Configuration

**Development Credentials** (SQLite backend/app.py):
- **Admin**: admin@politikos.com / AdminPass123
- **Analyst**: analyst@politikos.com / AnalystPass123  
- **User**: user@politikos.com / UserPass123

**Database**: SQLite (politikos_full.db) auto-created with sample data

**Environment**: 
- CORS: Pre-configured for localhost:3000, 3001, 3003
- Authentication: Simple token-based authentication
- Database: SQLite for development, PostgreSQL for production

**Current Architecture** (development):
```
backend/app.py (simplified SQLite)     # Main development server
├── politikos_full.db                 # SQLite database file
└── backup_old_servers/               # Complex implementations
```

## Key Technical Details

**Authentication**: Simple token-based auth in backend/app.py (bcrypt password hashing)
**Database**: SQLite with auto-initialization, includes sample users and data
**Frontend**: React + TypeScript + Ant Design components for UI
**Styling**: Component-specific CSS files (e.g., AnalyticsDashboard.css)

**Development Workflow**:
1. Backend: `cd backend && python app.py` (starts SQLite-based server on port 5000)
2. Frontend: `cd frontend && npm start` (React dev server on port 3000)
3. Database auto-created as politikos_full.db with sample data

**Production Architecture** (Docker Compose):
- PostgreSQL database with Redis caching
- Celery workers for background tasks
- Flower monitoring on port 5555
- Containerized deployment via scripts/deploy.sh

**Service Ports**:
- Frontend: http://localhost:3000 (dev), http://localhost:3000 (prod container)
- Backend API: http://localhost:5000
- PostgreSQL: port 5432 (prod)
- Redis: port 6379 (prod)
- Flower monitoring: http://localhost:5555 (prod)

# Development Notes

**Current State**: The project uses a simplified SQLite-based backend (backend/app.py) for development with a complete modular architecture (backend/app/) available for production use.

**Code Architecture**:
- Clean separation between development (SQLite) and production (PostgreSQL + Redis + Celery)
- Component-based React frontend with TypeScript and Ant Design
- Modular backend structure ready for scaling

**Testing**: Use `npm test` in frontend directory. Backend tests depend on specific test framework implementation.

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.