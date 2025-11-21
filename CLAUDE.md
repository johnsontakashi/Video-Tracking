# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Influencer Analytics Platform** - a comprehensive social media analytics system for tracking and analyzing influencer profiles across Instagram, YouTube, TikTok, and Twitter. The platform features user management, analytics dashboards, and role-based access control.

**🚀 RECENTLY REFACTORED (Nov 2025)**: The codebase has been cleaned up and simplified for better maintainability.

## Architecture

**Stack**: Flask (Python) + React (TypeScript) + SQLite (for development)
- **Backend**: Clean Flask API (app.py) with token authentication, role-based access control
- **Frontend**: React with TypeScript, Ant Design UI components, responsive dashboards  
- **Database**: SQLite with automatic initialization and sample data
- **Authentication**: Token-based authentication with proper validation
- **File Structure**: Simplified with unnecessary files moved to backup_old_servers/

## Development Commands

### Local Development Setup

**Backend (Python/Flask)**:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Frontend (React/TypeScript)**:
```bash
cd frontend
npm install
npm start      # Development server
npm run build  # Production build
npm test       # Run tests
```

**Database**:
```bash
# SQLite database is automatically initialized when running app.py
# No additional setup required - database creates itself with sample data
```

**Celery Workers**:
```bash
cd backend
celery -A app.celery worker --loglevel=info
celery -A app.celery beat --loglevel=info
```

### Production Deployment

```bash
# Deploy entire stack
chmod +x scripts/deploy.sh
./scripts/deploy.sh

# Backup database
./scripts/backup.sh --full

# Health check
./scripts/deploy.sh --health-check
```

### Container Management

```bash
# Start all services
docker-compose up -d

# Check service status  
docker-compose ps

# View logs
docker-compose logs [service-name]

# Restart services
docker-compose restart
```

## Key Directory Structure

```
├── backend/                 # Flask API server
│   ├── app/
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── services/       # Business logic and API services
│   │   ├── collectors/     # Social media data collection modules
│   │   ├── routes/         # API route definitions
│   │   ├── tasks/          # Celery background tasks
│   │   ├── utils/          # Utility functions
│   │   └── middleware/     # Authentication and security middleware
│   ├── migrations/         # Database migration files
│   └── requirements.txt    # Python dependencies
├── frontend/               # React application
│   ├── src/
│   │   ├── components/     # React components (organized by feature)
│   │   ├── services/       # API service functions
│   │   ├── contexts/       # React Context providers (Auth, etc.)
│   │   ├── utils/          # Frontend utility functions
│   │   └── styles/         # CSS and styling
│   └── package.json        # Node.js dependencies
└── scripts/                # Deployment and maintenance scripts
```

## Important Configuration

**Current Admin Credentials** (after refactoring):
- **Admin**: admin@politikos.com / AdminPass123
- **Analyst**: analyst@politikos.com / AnalystPass123  
- **User**: user@politikos.com / UserPass123

**Environment Setup**: Basic setup with `.env` file (optional for development):
- Database: SQLite (automatically created)
- Authentication: Token-based (no additional config needed)
- CORS: Pre-configured for localhost:3000, 3001, 3003

**Simplified File Structure** (after cleanup):
```
backend/
├── app.py              # Main clean Flask application (15KB)
├── config.py           # Configuration settings
├── run.py              # Alternative run script
├── requirements.txt    # Python dependencies
└── backup_old_servers/ # Old complex files moved here
```

## Authentication & Security

- **JWT-based authentication** with refresh tokens
- **Role-based access control**: admin, analyst, guest roles
- **Rate limiting** on API endpoints (Flask-Limiter)
- **bcrypt password hashing** with configurable rounds
- **Input validation** using Marshmallow schemas

## Data Collection Features

- **Multi-platform support**: Instagram, YouTube, TikTok, Twitter APIs
- **Proxy rotation** and rate limiting for web scraping
- **Celery background tasks** for data collection queues
- **Sentiment analysis** using TextBlob and NLTK (Portuguese/English)
- **Fallback mechanisms** between API providers and web scraping

## Frontend Architecture

- **React with TypeScript** for type safety
- **Ant Design components** for consistent UI
- **React Grid Layout** for drag-and-drop dashboards
- **Chart.js/Recharts** for data visualization
- **Context API** for state management (authentication, user data)

## Production Considerations

- **Containerized deployment** with Docker Compose
- **Database partitioning** for analytics tables by month
- **Redis caching** for frequently accessed data
- **Flower monitoring** for Celery task monitoring at port 5555
- **Health checks** and automated monitoring scripts
- **SSL certificate setup** via Let's Encrypt or self-signed for development

## Service Ports

- **Frontend**: http://localhost:3000 (dev), port 80 (prod)
- **Backend API**: http://localhost:5000
- **PostgreSQL**: port 5432
- **Redis**: port 6379  
- **Flower (Celery monitoring)**: http://localhost:5555

## Common Development Tasks

When working on this codebase:
- **Always run linting/type checks** before committing changes
- **Use existing component patterns** from the frontend codebase
- **Follow the authentication middleware** for protected routes
- **Test data collection features** in development mode first
- **Check Celery task queues** via Flower when debugging background jobs
- **Use database migrations** for schema changes via Flask-Migrate