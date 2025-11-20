# Influencer Analytics Platform

A comprehensive influencer analytics platform for tracking and analyzing social media influencers across multiple platforms (Instagram, YouTube, TikTok, Twitter).

## 🚀 Features

### Core Modules
- **📊 Influencer Data Collection**: Track 450k+ influencer profiles across major platforms
- **🧠 Data Processing & Analytics**: Advanced sentiment analysis and influence scoring
- **📈 Interactive Dashboard**: Drag-and-drop widgets with real-time updates
- **📋 Report Generation**: Automated PDF/Excel reports with email delivery
- **☁️ Production Deployment**: Docker-based deployment with SSL and monitoring
- **💳 Payment Integration**: Stripe subscription management with multiple plans

### Technical Highlights
- **Scalable Architecture**: Microservices with Flask + React + PostgreSQL + Redis
- **Advanced Analytics**: NLP sentiment analysis for Portuguese/English content
- **Data Collection**: Proxy rotation, rate limiting, and multi-platform APIs
- **Security**: JWT authentication, role-based access, encrypted backups
- **Performance**: Database partitioning, caching, and optimized queries
- **Monitoring**: Health checks, logging, and Flower for Celery monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │     Backend     │    │    Database     │
│   (React)       │◄──►│    (Flask)      │◄──►│  (PostgreSQL)   │
│   Port: 80      │    │   Port: 5000    │    │   Port: 5432    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │     Redis       │    │     Celery      │
         └──────────────│   (Cache)       │◄──►│   (Workers)     │
                        │   Port: 6379    │    │   + Flower      │
                        └─────────────────┘    └─────────────────┘
```

## 📦 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM
- 10GB+ storage

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd Video-Tracking
cp .env.example .env
```

2. **Configure Environment**
Edit `.env` file with your settings:
- Database passwords
- Secret keys (generate random strings)
- Stripe API keys
- Email configuration

3. **Deploy**
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

4. **Access the Platform**
- **Frontend**: http://localhost
- **API**: http://localhost:5000/api
- **Admin Panel**: http://localhost/admin
- **Flower Monitor**: http://localhost:5555
- **PgAdmin**: http://localhost:5050

### Default Credentials
- **Admin**: admin@yourdomain.com / change-this-password
- **PgAdmin**: admin@yourdomain.com / change-this-pgadmin-password
- **Flower**: admin / change-this-flower-password

⚠️ **Change all default passwords after first login!**

## 🛠️ Development

### Local Development Setup

1. **Backend Setup**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm start
```

3. **Database Setup**
```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Initialize database
python scripts/init_db.py

# Run migrations
flask db upgrade
```

4. **Start Services**
```bash
# Backend
cd backend && python app.py

# Frontend
cd frontend && npm start

# Celery Worker
cd backend && celery -A app.celery worker --loglevel=info

# Celery Beat (scheduler)
cd backend && celery -A app.celery beat --loglevel=info
```

### Project Structure

```
├── backend/
│   ├── app/
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── collectors/      # Data collection modules
│   │   ├── api/             # REST API endpoints
│   │   ├── tasks/           # Celery background tasks
│   │   └── utils/           # Utility functions
│   ├── migrations/          # Database migrations
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── services/        # API services
│   │   ├── utils/           # Utility functions
│   │   └── styles/          # CSS/styling
│   └── package.json         # Node dependencies
├── scripts/
│   ├── deploy.sh           # Production deployment
│   ├── backup.sh           # Backup management
│   └── init_db.py          # Database initialization
└── docker-compose.yml     # Container orchestration
```

## 📊 Database Schema

### Core Tables
- **users**: User accounts with role-based access
- **influencers**: Influencer profiles with platform data
- **influencer_analytics**: Time-series analytics data (partitioned)
- **collection_tasks**: Data collection job tracking
- **subscriptions**: Payment and subscription management

### Key Features
- **Partitioning**: Analytics table partitioned by month for performance
- **Indexing**: Optimized indexes for common queries
- **Relationships**: Proper foreign key relationships and constraints

## 🔒 Security

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (Admin, Premium, Basic)
- Password hashing with bcrypt
- Session management

### Data Protection
- Encrypted database backups
- Secure environment variable management
- SSL/TLS encryption
- Input validation and sanitization

### API Security
- Rate limiting (10 requests/second)
- CORS configuration
- Security headers (XSS, CSRF protection)
- Request validation

## 📈 Analytics Features

### Sentiment Analysis
- Multi-language support (Portuguese, English)
- Comment and post sentiment scoring
- Trend analysis over time
- Keyword extraction and analysis

### Influence Scoring
- Multi-factor algorithm considering:
  - Engagement rates
  - Follower growth
  - Content quality
  - Audience interaction
  - Platform reach

### Dashboard Widgets
- Drag-and-drop interface
- Real-time data updates
- Customizable layouts
- Export capabilities

## 💳 Payment Integration

### Subscription Plans
- **Basic** ($29/month): 100 influencers, 3-month history
- **Professional** ($99/month): 1,000 influencers, 12-month history  
- **Enterprise** ($299/month): Unlimited access

### Features
- Stripe payment processing
- Webhook handling for payment events
- Automatic subscription management
- Invoice generation and email delivery

## 🔧 Data Collection

### Supported Platforms
- **Instagram**: Posts, stories, reels, IGTV
- **YouTube**: Videos, shorts, community posts
- **TikTok**: Videos, live streams
- **Twitter**: Tweets, threads, spaces

### Collection Features
- Proxy rotation for rate limiting
- Multiple API providers (APIFY, BrightData)
- Fallback to web scraping
- Comprehensive error handling
- Retry logic with exponential backoff

## 📋 Monitoring & Maintenance

### Backup Management
```bash
# Full backup
./scripts/backup.sh --full

# Database only
./scripts/backup.sh --database

# List backups
./scripts/backup.sh --list

# Restore from backup
./scripts/backup.sh --restore /path/to/backup.sql.enc.gz
```

### Health Monitoring
- Automated service health checks
- Log rotation and management
- Performance monitoring with Flower
- Alert system for failures

### Maintenance Tasks
- Automated database cleanup
- Log archival
- Performance optimization
- Security updates

## 🚀 Production Deployment

### System Requirements
- **OS**: Ubuntu 20.04+ or CentOS 7+
- **RAM**: 8GB+ recommended
- **Storage**: 50GB+ SSD
- **Network**: 1GB bandwidth

### SSL Configuration
```bash
# Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Copy certificates
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /opt/ssl/influencer-analytics/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /opt/ssl/influencer-analytics/private.key
```

### Environment Variables
Key variables to configure:
- `SECRET_KEY`: Flask secret key (generate random)
- `JWT_SECRET_KEY`: JWT signing key (generate random)
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `STRIPE_SECRET_KEY`: Stripe API key
- `MAIL_*`: Email configuration
- `DOMAIN_NAME`: Your domain name

## 🤝 API Documentation

### Authentication
```bash
# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "password"
}

# Returns JWT token for authentication
```

### Influencer Data
```bash
# Get influencers
GET /api/influencers?platform=instagram&limit=50

# Get influencer details
GET /api/influencers/{id}

# Get influencer analytics
GET /api/influencers/{id}/analytics?days=30
```

### Dashboard API
```bash
# Get dashboard data
GET /api/dashboard/stats

# Save widget layout
POST /api/dashboard/layout
{
  "widgets": [...]
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Services not starting**
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs [service-name]

# Restart services
docker-compose restart
```

2. **Database connection errors**
```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Verify environment variables
grep DATABASE_URL .env
```

3. **Frontend not loading**
```bash
# Check nginx logs
docker-compose logs frontend

# Verify API connection
curl http://localhost:5000/api/health
```

### Performance Optimization

1. **Database tuning**
   - Monitor slow queries
   - Adjust PostgreSQL settings
   - Regular VACUUM and ANALYZE

2. **Redis optimization**
   - Monitor memory usage
   - Configure eviction policies
   - Optimize key expiration

3. **Application tuning**
   - Monitor Celery worker performance
   - Adjust worker counts
   - Optimize collection intervals

## 📞 Support

For issues and support:
1. Check the troubleshooting section
2. Review application logs
3. Check system resources
4. Verify configuration

## 📄 License

This project is proprietary software. All rights reserved.

---

**Built with ❤️ for influencer analytics and social media intelligence.**