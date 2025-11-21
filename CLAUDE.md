# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an **Influencer Analytics Platform** - a comprehensive social media analytics system for tracking and analyzing 450k+ influencer profiles across Instagram, YouTube, TikTok, and Twitter. The platform features advanced sentiment analysis, real-time dashboards, payment integration, and automated data collection.

## Architecture

**Stack**: Flask (Python) + React (TypeScript) + PostgreSQL + Redis + Celery
- **Backend**: Flask API with JWT authentication, role-based access control, Celery background tasks
- **Frontend**: React with TypeScript, Ant Design UI components, drag-and-drop dashboards  
- **Database**: PostgreSQL with partitioned analytics tables for performance
- **Cache/Queue**: Redis for caching and Celery task management
- **Deployment**: Docker containers with production-ready setup

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
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Initialize database
python scripts/init_db.py

# Run migrations
flask db upgrade
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

**Environment Setup**: Copy `.env.example` to `.env` and configure:
- Database credentials (PostgreSQL)
- Redis password and connection
- JWT secret keys (generate random strings for production)
- Stripe API keys for payment processing  
- Email configuration for notifications

**Database Schema**: Key tables include partitioned `influencer_analytics` for time-series data, `users` with role-based access control, and `collection_tasks` for tracking data gathering jobs.

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