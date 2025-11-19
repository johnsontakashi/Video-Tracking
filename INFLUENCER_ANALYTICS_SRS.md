# 🎯 Influencer Analytics Platform - Software Requirements Specification

**Version**: 1.0  
**Date**: 2024-01-01  
**Project**: Video Tracking + Influencer Analytics Platform

---

## 📋 Table of Contents

1. [Module Overview](#1-module-overview)
2. [Database Schema](#2-database-schema)
3. [Backend Architecture & Folder Structure](#3-backend-architecture--folder-structure)
4. [Celery Worker & Task Scheduling Flow](#4-celery-worker--task-scheduling-flow)
5. [Frontend Component Structure](#5-frontend-component-structure)
6. [API Endpoints & Sample Requests/Responses](#6-api-endpoints--sample-requestsresponses)
7. [Data Flow Diagrams](#7-data-flow-diagrams)
8. [Security & Rate Limit Considerations](#8-security--rate-limit-considerations)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Testing Strategy](#10-testing-strategy)
11. [Future Expansion Notes](#11-future-expansion-notes)

---

## 1. Module Overview

### 1.1 System Architecture

```ascii
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   API Gateway   │    │  Data Pipeline  │
│   (React/TS)    │◄──►│   (Flask)       │◄──►│  (Celery/Redis) │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • Auth/Users    │    │ • Collection    │
│ • Reports       │    │ • Analytics     │    │ • Processing    │
│ • Payments      │    │ • Payments      │    │ • Analysis      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CDN/Assets    │    │   PostgreSQL    │    │   Redis Cluster │
│   (Static)      │    │   (Main DB)     │    │ (Cache/Queue)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 1.2 Core Modules

#### **1. Data Collector Module**
- **Purpose**: Parallel collection from 450k+ influencer profiles
- **Platforms**: Instagram, YouTube, TikTok, X(Twitter)
- **APIs**: APIFY, BrightData, platform APIs
- **Scale**: Distributed workers with proxy rotation

#### **2. Analytics Engine**
- **Purpose**: Real-time data processing and NLP analysis
- **Features**: Sentiment analysis, keyword extraction, influence scoring
- **Languages**: Portuguese + English support
- **Output**: Structured analytics for dashboard consumption

#### **3. Dashboard Interface**
- **Purpose**: Interactive analytics visualization
- **Features**: Drag-drop widgets, real-time updates, custom layouts
- **Charts**: Line, bar, heatmap, wordcloud, trend analysis

#### **4. Report Generator**
- **Purpose**: Automated PDF/Excel report creation
- **Features**: Scheduled delivery, custom templates
- **Integration**: Email automation, storage

#### **5. Payment System**
- **Purpose**: Subscription management and billing
- **Providers**: Stripe, MercadoPago
- **Features**: Webhooks, access control, billing cycles

#### **6. Infrastructure Layer**
- **Purpose**: Scalable deployment and monitoring
- **Components**: Nginx, Gunicorn, SSL, load balancing

---

## 2. Database Schema

### 2.1 Complete ERD Diagram

```ascii
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│     Users       │    │   Subscriptions  │    │    Platforms    │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ id (PK)         │◄──┤ user_id (FK)     │    │ id (PK)         │
│ email           │    │ plan_type        │    │ name            │
│ subscription_id │    │ status           │    │ api_endpoint    │
│ role            │    │ current_period   │    │ rate_limits     │
│ created_at      │    │ stripe_sub_id    │    │ active          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Influencers   │    │   Collections    │    │     Posts       │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ id (PK)         │◄──┤ influencer_id    │    │ id (PK)         │
│ platform_id     │    │ user_id (FK)     │    │ influencer_id   │
│ username        │    │ status           │    │ platform_id     │
│ display_name    │    │ started_at       │    │ external_id     │
│ follower_count  │    │ completed_at     │    │ content         │
│ verified        │    │ error_count      │    │ created_at      │
│ profile_url     │    │ collected_posts  │    │ likes           │
│ last_updated    │    └──────────────────┘    │ comments        │
└─────────────────┘                            │ shares          │
         │                                     │ views           │
         ▼                                     │ raw_data (JSON) │
┌─────────────────┐    ┌──────────────────┐    └─────────────────┘
│   Analytics     │    │    Comments      │               │
├─────────────────┤    ├──────────────────┤               ▼
│ id (PK)         │    │ id (PK)          │    ┌─────────────────┐
│ influencer_id   │    │ post_id (FK)     │    │   Sentiments    │
│ influence_score │    │ author_name      │    ├─────────────────┤
│ sentiment_avg   │    │ content          │    │ id (PK)         │
│ engagement_rate │    │ likes            │    │ post_id (FK)    │
│ trend_score     │    │ created_at       │    │ comment_id (FK) │
│ keywords (JSON) │    │ sentiment_score  │    │ score           │
│ computed_at     │    └──────────────────┘    │ language        │
└─────────────────┘                            │ confidence      │
         │                                     │ keywords (JSON) │
         ▼                                     └─────────────────┘
┌─────────────────┐    ┌──────────────────┐    
│    Reports      │    │   Dashboards     │    ┌─────────────────┐
├─────────────────┤    ├──────────────────┤    │  Collection     │
│ id (PK)         │    │ id (PK)          │    │  Tasks          │
│ user_id (FK)    │    │ user_id (FK)     │    ├─────────────────┤
│ title           │    │ name             │    │ id (PK)         │
│ template_id     │    │ layout (JSON)    │    │ task_id (UUID)  │
│ parameters      │    │ widgets (JSON)   │    │ influencer_id   │
│ format (PDF/XL) │    │ is_default       │    │ status          │
│ generated_at    │    │ created_at       │    │ priority        │
│ file_path       │    └──────────────────┘    │ attempts        │
│ email_sent      │                            │ scheduled_at    │
└─────────────────┘                            │ started_at      │
                                               │ completed_at    │
┌─────────────────┐    ┌──────────────────┐    │ error_message   │
│   Proxies       │    │  Rate Limits     │    │ result (JSON)   │
├─────────────────┤    ├──────────────────┤    └─────────────────┘
│ id (PK)         │    │ id (PK)          │              │
│ host            │    │ endpoint         │              ▼
│ port            │    │ requests_per_min │    ┌─────────────────┐
│ username        │    │ current_count    │    │  Error Logs     │
│ password        │    │ reset_at         │    ├─────────────────┤
│ protocol        │    │ platform_id      │    │ id (PK)         │
│ is_active       │    └──────────────────┘    │ task_id (FK)    │
│ success_rate    │                            │ error_type      │
│ last_used       │                            │ message         │
└─────────────────┘                            │ traceback       │
                                               │ retry_count     │
                                               │ created_at      │
                                               └─────────────────┘
```

### 2.2 Key Schema Optimizations

#### **Partitioning Strategy**
```sql
-- Partition posts by platform and date for performance
CREATE TABLE posts (
    id BIGSERIAL,
    influencer_id BIGINT NOT NULL,
    platform_id INT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    -- ... other fields
) PARTITION BY RANGE (created_at);

CREATE TABLE posts_2024_q1 PARTITION OF posts 
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');
```

#### **Indexing Strategy**
```sql
-- Composite indexes for common queries
CREATE INDEX idx_posts_influencer_date ON posts (influencer_id, created_at DESC);
CREATE INDEX idx_analytics_score_date ON analytics (influence_score DESC, computed_at);
CREATE INDEX idx_comments_sentiment ON comments (sentiment_score, post_id);

-- Partial indexes for active data
CREATE INDEX idx_active_influencers ON influencers (id) WHERE last_updated > NOW() - INTERVAL '30 days';
```

---

## 3. Backend Architecture & Folder Structure

### 3.1 Optimized Folder Structure

```
backend/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config/
│   │   ├── __init__.py
│   │   ├── base.py                 # Base configuration
│   │   ├── development.py          # Dev settings
│   │   ├── production.py           # Prod settings
│   │   └── testing.py              # Test settings
│   │
│   ├── models/                     # Database models
│   │   ├── __init__.py
│   │   ├── base.py                 # Base model class
│   │   ├── user.py                 # User & auth models
│   │   ├── influencer.py           # Influencer data models
│   │   ├── analytics.py            # Analytics & metrics
│   │   ├── collection.py           # Collection tasks & logs
│   │   ├── subscription.py         # Payment & billing
│   │   └── dashboard.py            # Dashboard layouts
│   │
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Authentication logic
│   │   ├── collection_service.py   # Data collection orchestration
│   │   ├── analytics_service.py    # NLP & scoring algorithms
│   │   ├── dashboard_service.py    # Dashboard data preparation
│   │   ├── report_service.py       # Report generation
│   │   ├── payment_service.py      # Stripe/payment logic
│   │   └── notification_service.py # Email & alerts
│   │
│   ├── collectors/                 # Data collection modules
│   │   ├── __init__.py
│   │   ├── base_collector.py       # Abstract base collector
│   │   ├── instagram_collector.py  # Instagram API integration
│   │   ├── youtube_collector.py    # YouTube API integration
│   │   ├── tiktok_collector.py     # TikTok API integration
│   │   ├── twitter_collector.py    # X/Twitter API integration
│   │   ├── apify_collector.py      # APIFY integration
│   │   └── brightdata_collector.py # BrightData integration
│   │
│   ├── processors/                 # Data processing pipeline
│   │   ├── __init__.py
│   │   ├── base_processor.py       # Abstract processor
│   │   ├── content_cleaner.py      # Text cleaning & normalization
│   │   ├── sentiment_analyzer.py   # Portuguese/English sentiment
│   │   ├── keyword_extractor.py    # TF-IDF & embeddings
│   │   ├── influence_scorer.py     # Influence score algorithm
│   │   └── trend_detector.py       # Trend analysis
│   │
│   ├── tasks/                      # Celery tasks
│   │   ├── __init__.py
│   │   ├── collection_tasks.py     # Data collection tasks
│   │   ├── processing_tasks.py     # Data processing tasks
│   │   ├── analytics_tasks.py      # Analytics computation
│   │   ├── report_tasks.py         # Report generation tasks
│   │   └── maintenance_tasks.py    # Cleanup & maintenance
│   │
│   ├── api/                        # API routes
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── influencers.py      # Influencer CRUD
│   │   │   ├── analytics.py        # Analytics data
│   │   │   ├── dashboard.py        # Dashboard API
│   │   │   ├── reports.py          # Report endpoints
│   │   │   ├── collections.py      # Collection management
│   │   │   └── payments.py         # Payment & subscription
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── security.py             # Security helpers
│   │   ├── validators.py           # Input validation
│   │   ├── decorators.py           # Custom decorators
│   │   ├── rate_limiter.py         # Rate limiting logic
│   │   ├── proxy_manager.py        # Proxy rotation
│   │   ├── cache.py                # Caching utilities
│   │   └── exceptions.py           # Custom exceptions
│   │
│   ├── middleware/                 # Custom middleware
│   │   ├── __init__.py
│   │   ├── auth_middleware.py      # JWT & role validation
│   │   ├── rate_limit_middleware.py # Rate limiting
│   │   ├── cors_middleware.py      # CORS handling
│   │   └── error_middleware.py     # Error handling
│   │
│   └── extensions.py               # Flask extensions initialization
│
├── migrations/                     # Database migrations
├── tests/                         # Test suite
├── scripts/                       # Utility scripts
├── requirements/                  # Environment-specific requirements
├── docker/                        # Docker configurations
├── run.py                         # Application entry point
└── celery_app.py                  # Celery worker entry point
```

### 3.2 Core Architecture Patterns

#### **Service Layer Pattern**
```python
# app/services/collection_service.py
class CollectionService:
    def __init__(self, collector_factory, task_queue):
        self.collector_factory = collector_factory
        self.task_queue = task_queue
    
    async def collect_influencer_data(self, influencer_id: int, platforms: List[str]):
        """Orchestrate parallel data collection across platforms"""
        tasks = []
        for platform in platforms:
            collector = self.collector_factory.create_collector(platform)
            task = self.task_queue.delay('collect_platform_data', 
                                       influencer_id, platform)
            tasks.append(task)
        
        return await self.monitor_collection_tasks(tasks)
```

#### **Factory Pattern for Collectors**
```python
# app/collectors/factory.py
class CollectorFactory:
    _collectors = {
        'instagram': InstagramCollector,
        'youtube': YoutubeCollector,
        'tiktok': TiktokCollector,
        'twitter': TwitterCollector,
    }
    
    @classmethod
    def create_collector(cls, platform: str) -> BaseCollector:
        if platform not in cls._collectors:
            raise ValueError(f"Unsupported platform: {platform}")
        return cls._collectors[platform]()
```

---

## 4. Celery Worker & Task Scheduling Flow

### 4.1 Worker Architecture

```ascii
┌─────────────────────────────────────────────────────────────┐
│                    Celery Architecture                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Flask Web App  │    │  Celery Beat    │    │ Redis Cluster   │
│                 │    │  (Scheduler)    │    │                 │
│ • Submit tasks  │───►│ • Cron jobs     │───►│ • Task queues   │
│ • Monitor jobs  │    │ • Recurring     │    │ • Results       │
│ • Get results   │    │   tasks         │    │ • Locks         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Pools                              │
├─────────────────┬─────────────────┬─────────────────────────┤
│ Collection Pool │ Processing Pool │    Analytics Pool       │
│                 │                 │                         │
│ • 50 workers    │ • 20 workers    │ • 10 workers           │
│ • Platform APIs │ • NLP tasks     │ • Score computation    │
│ • Rate limiting │ • Data cleaning │ • Trend analysis       │
│ • Proxy rotation│ • Deduplication │ • Report generation    │
└─────────────────┴─────────────────┴─────────────────────────┘
```

### 4.2 Task Priority & Routing

```python
# app/tasks/collection_tasks.py
from celery import Celery
from kombu import Queue

# Queue configuration with priority routing
app = Celery('influencer_analytics')
app.conf.task_routes = {
    'tasks.collection.*': {'queue': 'collection', 'routing_key': 'collection'},
    'tasks.processing.*': {'queue': 'processing', 'routing_key': 'processing'},
    'tasks.analytics.*': {'queue': 'analytics', 'routing_key': 'analytics'},
    'tasks.reports.*': {'queue': 'reports', 'routing_key': 'reports'},
}

app.conf.task_queues = (
    Queue('collection', routing_key='collection', 
          message_ttl=3600, max_priority=10),
    Queue('processing', routing_key='processing', 
          message_ttl=1800, max_priority=5),
    Queue('analytics', routing_key='analytics', 
          message_ttl=3600, max_priority=3),
    Queue('reports', routing_key='reports', 
          message_ttl=7200, max_priority=1),
)

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
def collect_influencer_posts(self, influencer_id: int, platform: str):
    """Collect posts for specific influencer on platform"""
    try:
        collector = CollectorFactory.create_collector(platform)
        
        with ProxyManager() as proxy:
            posts = collector.collect_posts(influencer_id, proxy=proxy)
            
        # Store raw data
        for post in posts:
            Post.create_from_raw_data(post, influencer_id, platform)
            
        # Trigger processing pipeline
        process_influencer_content.delay(influencer_id, platform)
        
        return {'status': 'success', 'posts_collected': len(posts)}
        
    except RateLimitException as e:
        # Exponential backoff for rate limits
        raise self.retry(countdown=2 ** self.request.retries * 60)
    except ProxyException as e:
        # Switch proxy and retry
        raise self.retry(countdown=30)
```

### 4.3 Scheduled Tasks (Celery Beat)

```python
# app/tasks/scheduled_tasks.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    # Hourly analytics processing
    'process-analytics-hourly': {
        'task': 'tasks.analytics.compute_hourly_metrics',
        'schedule': crontab(minute=0),  # Every hour
        'kwargs': {'batch_size': 1000}
    },
    
    # Daily influence score computation
    'compute-influence-scores': {
        'task': 'tasks.analytics.compute_influence_scores',
        'schedule': crontab(hour=2, minute=0),  # 2 AM daily
    },
    
    # Weekly reports generation
    'generate-weekly-reports': {
        'task': 'tasks.reports.generate_scheduled_reports',
        'schedule': crontab(day_of_week=1, hour=8, minute=0),  # Monday 8 AM
        'kwargs': {'report_type': 'weekly'}
    },
    
    # Proxy health check
    'check-proxy-health': {
        'task': 'tasks.maintenance.check_proxy_health',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    
    # Database cleanup
    'cleanup-old-data': {
        'task': 'tasks.maintenance.cleanup_old_data',
        'schedule': crontab(hour=3, minute=0),  # 3 AM daily
        'kwargs': {'days_to_keep': 90}
    }
}
```

### 4.4 Error Handling & Retry Logic

```python
# app/utils/task_decorators.py
from functools import wraps
import logging

def robust_task(max_retries=3, backoff_factor=2, exceptions=(Exception,)):
    """Decorator for robust task execution with exponential backoff"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except exceptions as exc:
                if self.request.retries < max_retries:
                    countdown = backoff_factor ** self.request.retries * 60
                    logging.warning(f"Task {func.__name__} failed, retrying in {countdown}s")
                    raise self.retry(countdown=countdown, exc=exc)
                else:
                    logging.error(f"Task {func.__name__} failed permanently: {exc}")
                    # Store error in database for debugging
                    ErrorLog.create(
                        task_id=self.request.id,
                        error_type=type(exc).__name__,
                        message=str(exc),
                        retry_count=self.request.retries
                    )
                    raise exc
        return wrapper
    return decorator
```

---

## 5. Frontend Component Structure

### 5.1 React Component Architecture

```
frontend/src/
├── components/
│   ├── common/                     # Reusable components
│   │   ├── Layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── UI/
│   │   │   ├── Button/
│   │   │   ├── Input/
│   │   │   ├── Modal/
│   │   │   ├── Table/
│   │   │   ├── Chart/
│   │   │   └── Loading/
│   │   └── Form/
│   │       ├── FormField.tsx
│   │       ├── ValidationError.tsx
│   │       └── FormSubmit.tsx
│   │
│   ├── auth/                       # Authentication components
│   │   ├── LoginForm.tsx
│   │   ├── SignupForm.tsx
│   │   ├── PasswordReset.tsx
│   │   └── ProtectedRoute.tsx
│   │
│   ├── dashboard/                  # Dashboard components
│   │   ├── DashboardLayout.tsx
│   │   ├── WidgetGrid.tsx
│   │   ├── widgets/
│   │   │   ├── BaseWidget.tsx      # Widget base class
│   │   │   ├── InfluenceScore.tsx
│   │   │   ├── TrendChart.tsx
│   │   │   ├── SentimentMeter.tsx
│   │   │   ├── TopInfluencers.tsx
│   │   │   ├── WordCloud.tsx
│   │   │   ├── EngagementRate.tsx
│   │   │   └── RealtimeMetrics.tsx
│   │   ├── DragDropProvider.tsx
│   │   └── WidgetCustomizer.tsx
│   │
│   ├── influencers/                # Influencer management
│   │   ├── InfluencerList.tsx
│   │   ├── InfluencerProfile.tsx
│   │   ├── InfluencerSearch.tsx
│   │   ├── InfluencerComparison.tsx
│   │   ├── AddInfluencer.tsx
│   │   └── BulkActions.tsx
│   │
│   ├── analytics/                  # Analytics components
│   │   ├── AnalyticsOverview.tsx
│   │   ├── SentimentAnalysis.tsx
│   │   ├── TrendAnalysis.tsx
│   │   ├── KeywordAnalysis.tsx
│   │   ├── InfluenceScoring.tsx
│   │   └── CompetitorAnalysis.tsx
│   │
│   ├── reports/                    # Report components
│   │   ├── ReportBuilder.tsx
│   │   ├── ReportPreview.tsx
│   │   ├── ReportScheduler.tsx
│   │   ├── ReportHistory.tsx
│   │   ├── templates/
│   │   │   ├── WeeklyTemplate.tsx
│   │   │   ├── MonthlyTemplate.tsx
│   │   │   └── CustomTemplate.tsx
│   │   └── ExportOptions.tsx
│   │
│   ├── collection/                 # Data collection UI
│   │   ├── CollectionDashboard.tsx
│   │   ├── CollectionQueue.tsx
│   │   ├── CollectionStatus.tsx
│   │   ├── PlatformSettings.tsx
│   │   └── CollectionLogs.tsx
│   │
│   └── billing/                    # Payment components
│       ├── SubscriptionPlan.tsx
│       ├── PaymentMethod.tsx
│       ├── BillingHistory.tsx
│       ├── UpgradeModal.tsx
│       └── UsageMetrics.tsx
│
├── hooks/                          # Custom React hooks
│   ├── useAuth.ts
│   ├── useApi.ts
│   ├── useWebSocket.ts
│   ├── useDragDrop.ts
│   ├── useChartData.ts
│   ├── useInfiniteScroll.ts
│   └── useLocalStorage.ts
│
├── contexts/                       # React contexts
│   ├── AuthContext.tsx
│   ├── ThemeContext.tsx
│   ├── DashboardContext.tsx
│   └── WebSocketContext.tsx
│
├── services/                       # API services
│   ├── api.ts                      # Base API client
│   ├── authService.ts
│   ├── influencerService.ts
│   ├── analyticsService.ts
│   ├── dashboardService.ts
│   ├── reportService.ts
│   ├── collectionService.ts
│   └── paymentService.ts
│
├── utils/                          # Utility functions
│   ├── formatters.ts               # Data formatting
│   ├── validators.ts               # Form validation
│   ├── constants.ts                # App constants
│   ├── helpers.ts                  # Helper functions
│   └── chartConfig.ts              # Chart configurations
│
├── types/                          # TypeScript definitions
│   ├── api.ts
│   ├── dashboard.ts
│   ├── influencer.ts
│   ├── analytics.ts
│   └── common.ts
│
└── styles/                         # Styling
    ├── globals.css
    ├── variables.css
    ├── components/
    └── themes/
```

### 5.2 Dashboard Widget System

```typescript
// components/dashboard/widgets/BaseWidget.tsx
interface WidgetProps {
  id: string;
  title: string;
  size: 'small' | 'medium' | 'large';
  data?: any;
  config?: WidgetConfig;
  onUpdate?: (data: any) => void;
  onResize?: (size: WidgetSize) => void;
  onRemove?: () => void;
}

interface WidgetConfig {
  refreshInterval?: number;
  filters?: Record<string, any>;
  chartType?: 'line' | 'bar' | 'pie' | 'heatmap';
  colorScheme?: string;
  showLegend?: boolean;
  dateRange?: DateRange;
}

abstract class BaseWidget extends React.Component<WidgetProps> {
  abstract renderContent(): React.ReactNode;
  abstract getDataRequirements(): DataRequirement[];
  
  render() {
    return (
      <div className={`widget widget-${this.props.size}`}>
        <WidgetHeader 
          title={this.props.title}
          onResize={this.props.onResize}
          onRemove={this.props.onRemove}
        />
        <WidgetBody>
          {this.renderContent()}
        </WidgetBody>
      </div>
    );
  }
}

// Drag & Drop Implementation
// components/dashboard/DragDropProvider.tsx
import { DndProvider, useDrag, useDrop } from 'react-dnd';

export const DashboardGrid: React.FC = () => {
  const [widgets, setWidgets] = useState<Widget[]>([]);
  const [layout, setLayout] = useState<Layout>();
  
  const moveWidget = useCallback((dragIndex: number, dropIndex: number) => {
    const dragWidget = widgets[dragIndex];
    const updatedWidgets = [...widgets];
    updatedWidgets.splice(dragIndex, 1);
    updatedWidgets.splice(dropIndex, 0, dragWidget);
    setWidgets(updatedWidgets);
    
    // Save layout to backend
    dashboardService.saveLayout(layout.id, updatedWidgets);
  }, [widgets, layout]);
  
  return (
    <DndProvider backend={HTML5Backend}>
      <ResponsiveGridLayout
        layouts={layout}
        onLayoutChange={handleLayoutChange}
        cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
      >
        {widgets.map((widget, index) => (
          <DraggableWidget
            key={widget.id}
            index={index}
            widget={widget}
            moveWidget={moveWidget}
          />
        ))}
      </ResponsiveGridLayout>
    </DndProvider>
  );
};
```

### 5.3 Real-time Updates with WebSocket

```typescript
// hooks/useWebSocket.ts
import { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';

export const useWebSocket = (endpoint: string) => {
  const [data, setData] = useState<any>(null);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<any>(null);
  
  useEffect(() => {
    socketRef.current = io(`${API_BASE_URL}${endpoint}`, {
      auth: { token: getAuthToken() }
    });
    
    socketRef.current.on('connect', () => setConnected(true));
    socketRef.current.on('disconnect', () => setConnected(false));
    socketRef.current.on('data_update', setData);
    
    return () => socketRef.current?.disconnect();
  }, [endpoint]);
  
  const sendMessage = useCallback((event: string, data: any) => {
    socketRef.current?.emit(event, data);
  }, []);
  
  return { data, connected, sendMessage };
};

// Real-time metrics component
// components/dashboard/widgets/RealtimeMetrics.tsx
export const RealtimeMetrics: React.FC<WidgetProps> = ({ config }) => {
  const { data: metrics, connected } = useWebSocket('/realtime/metrics');
  const [chartData, setChartData] = useState<ChartData>([]);
  
  useEffect(() => {
    if (metrics) {
      setChartData(prev => [...prev.slice(-50), {
        timestamp: new Date(),
        value: metrics.influence_score,
        engagement: metrics.engagement_rate
      }]);
    }
  }, [metrics]);
  
  return (
    <div className="realtime-widget">
      <div className="connection-status">
        <StatusDot color={connected ? 'green' : 'red'} />
        {connected ? 'Live' : 'Disconnected'}
      </div>
      
      <LineChart
        data={chartData}
        xKey="timestamp"
        yKeys={['value', 'engagement']}
        animate={true}
        showTooltip={true}
      />
      
      <MetricsGrid metrics={metrics} />
    </div>
  );
};
```

---

## 6. API Endpoints & Sample Requests/Responses

### 6.1 Authentication & User Management

#### **POST /api/v1/auth/login**
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
  "refresh_token": "secure_token_here",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "analyst",
    "subscription": {
      "plan": "pro",
      "expires_at": "2024-12-31T23:59:59Z",
      "features": ["unlimited_influencers", "advanced_analytics", "custom_reports"]
    }
  }
}
```

### 6.2 Influencer Management

#### **GET /api/v1/influencers**
```json
// Request Query Parameters
{
  "page": 1,
  "per_page": 50,
  "platform": "instagram",
  "min_followers": 10000,
  "verified": true,
  "sort": "influence_score",
  "order": "desc"
}

// Response (200)
{
  "success": true,
  "data": [
    {
      "id": 123,
      "username": "tech_influencer",
      "display_name": "Tech Guru",
      "platform": "instagram",
      "follower_count": 150000,
      "verified": true,
      "profile_image": "https://cdn.example.com/profile.jpg",
      "bio": "Technology enthusiast and content creator",
      "metrics": {
        "influence_score": 85,
        "engagement_rate": 4.2,
        "avg_likes": 5000,
        "avg_comments": 150
      },
      "last_updated": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 1250,
    "pages": 25
  }
}
```

#### **POST /api/v1/influencers/{id}/collect**
```json
// Request
{
  "platforms": ["instagram", "youtube"],
  "data_types": ["posts", "comments", "metrics"],
  "date_range": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  },
  "priority": "high"
}

// Response (202)
{
  "success": true,
  "collection_id": "coll_12345",
  "tasks": [
    {
      "task_id": "task_ig_67890",
      "platform": "instagram",
      "status": "queued",
      "estimated_duration": 300
    },
    {
      "task_id": "task_yt_67891",
      "platform": "youtube", 
      "status": "queued",
      "estimated_duration": 180
    }
  ],
  "message": "Collection tasks queued successfully"
}
```

### 6.3 Analytics API

#### **GET /api/v1/analytics/influence-scores**
```json
// Request Query Parameters
{
  "influencer_ids": [123, 456, 789],
  "date_range": "7d",
  "granularity": "daily"
}

// Response (200)
{
  "success": true,
  "data": {
    "123": {
      "current_score": 85,
      "score_history": [
        {"date": "2024-01-08", "score": 82},
        {"date": "2024-01-09", "score": 83},
        {"date": "2024-01-10", "score": 85}
      ],
      "score_breakdown": {
        "content_quality": 30,
        "engagement_rate": 25,
        "follower_growth": 15,
        "sentiment_score": 15
      }
    }
  }
}
```

#### **GET /api/v1/analytics/sentiment**
```json
// Request Query Parameters
{
  "influencer_id": 123,
  "platform": "instagram",
  "content_type": "posts",
  "date_range": "30d"
}

// Response (200)
{
  "success": true,
  "data": {
    "overall_sentiment": {
      "positive": 0.65,
      "neutral": 0.25,
      "negative": 0.10,
      "score": 0.55
    },
    "sentiment_timeline": [
      {
        "date": "2024-01-01",
        "positive": 0.70,
        "neutral": 0.20,
        "negative": 0.10
      }
    ],
    "top_keywords": {
      "positive": ["amazing", "love", "great", "awesome"],
      "negative": ["disappointed", "poor", "terrible"]
    },
    "language_breakdown": {
      "portuguese": 0.60,
      "english": 0.35,
      "spanish": 0.05
    }
  }
}
```

### 6.4 Dashboard API

#### **GET /api/v1/dashboard/layouts**
```json
// Response (200)
{
  "success": true,
  "layouts": [
    {
      "id": "layout_1",
      "name": "Analytics Overview",
      "is_default": true,
      "widgets": [
        {
          "id": "widget_1",
          "type": "influence_score",
          "position": {"x": 0, "y": 0, "w": 6, "h": 4},
          "config": {
            "influencer_ids": [123, 456],
            "chart_type": "line",
            "refresh_interval": 300
          }
        }
      ],
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### 6.5 Report Generation

#### **POST /api/v1/reports/generate**
```json
// Request
{
  "template_id": "weekly_analytics",
  "parameters": {
    "influencer_ids": [123, 456, 789],
    "date_range": {
      "start": "2024-01-01",
      "end": "2024-01-07"
    },
    "sections": ["overview", "sentiment", "trends", "recommendations"]
  },
  "format": "pdf",
  "delivery": {
    "email": "user@example.com",
    "schedule": null
  }
}

// Response (202)
{
  "success": true,
  "report_id": "report_12345",
  "status": "generating",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "download_url": null
}
```

### 6.6 Payment & Subscription

#### **POST /api/v1/payments/create-subscription**
```json
// Request
{
  "plan_id": "pro_monthly",
  "payment_method": "card",
  "billing_details": {
    "name": "John Doe",
    "email": "john@example.com",
    "address": {
      "line1": "123 Main St",
      "city": "São Paulo",
      "country": "BR",
      "postal_code": "01234-567"
    }
  }
}

// Response (201)
{
  "success": true,
  "subscription": {
    "id": "sub_12345",
    "plan": "pro_monthly",
    "status": "active",
    "current_period_start": "2024-01-15T00:00:00Z",
    "current_period_end": "2024-02-15T00:00:00Z",
    "features": {
      "max_influencers": 1000,
      "data_retention_days": 365,
      "api_rate_limit": 10000,
      "custom_reports": true
    }
  },
  "payment": {
    "amount": 9900,
    "currency": "brl",
    "status": "succeeded"
  }
}
```

---

## 7. Data Flow Diagrams

### 7.1 Collection Pipeline

```ascii
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Flow                      │
└─────────────────────────────────────────────────────────────┘

[User Request] ──► [Collection API] ──► [Task Queue]
                         │                   │
                         ▼                   ▼
                  [Validation &         [Celery Workers]
                   Rate Check]               │
                         │                   ▼
                         ▼              ┌─────────────┐
                   [Store Request]      │ Collector   │
                         │              │   Pool      │
                         ▼              │             │
┌─────────────────────────────────────────────────────────────┐
│             Platform API Calls                              │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ Instagram   │  YouTube    │   TikTok    │    X/Twitter    │
│ Collector   │ Collector   │ Collector   │   Collector     │
└─────────────┴─────────────┴─────────────┴─────────────────┘
       │              │            │              │
       ▼              ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│                Raw Data Storage                              │
├─────────────────────────────────────────────────────────────┤
│ • JSON blobs in PostgreSQL                                  │
│ • Partitioned by platform and date                         │
│ • Indexed for fast retrieval                               │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                Processing Pipeline                           │
├──────────────┬──────────────┬──────────────┬────────────────┤
│ Data Cleaning│  Sentiment   │  Keyword     │ Influence      │
│ & Validation │  Analysis    │  Extraction  │ Scoring        │
└──────────────┴──────────────┴──────────────┴────────────────┘
                         │
                         ▼
                 [Analytics Database]
                         │
                         ▼
                  [Dashboard & APIs]
```

### 7.2 Real-time Analytics Flow

```ascii
┌─────────────────────────────────────────────────────────────┐
│                Real-time Analytics Flow                      │
└─────────────────────────────────────────────────────────────┘

[New Data] ──► [Event Stream] ──► [Processing Workers]
    │               │                     │
    ▼               ▼                     ▼
[Database]    [Redis Pub/Sub]      [Analytics Engine]
    │               │                     │
    │               ▼                     ▼
    │         [WebSocket Server]    [Score Update]
    │               │                     │
    ▼               ▼                     ▼
[Dashboard]   [Frontend Updates]   [Cache Refresh]
                    │
                    ▼
              [Real-time UI]
```

### 7.3 Report Generation Flow

```ascii
┌─────────────────────────────────────────────────────────────┐
│                 Report Generation Flow                       │
└─────────────────────────────────────────────────────────────┘

[User Request] ──► [Report API] ──► [Template Engine]
                        │                 │
                        ▼                 ▼
                [Parameter         [Data Aggregation]
                 Validation]              │
                        │                 ▼
                        ▼           [Analytics Query]
                [Queue Report              │
                    Task]                  ▼
                        │            [Chart Generation]
                        ▼                 │
              ┌─────────────────┐         ▼
              │ Report Worker   │   [PDF/Excel Export]
              │                 │         │
              │ • Data fetch    │         ▼
              │ • Template      │    [File Storage]
              │ • Generation    │         │
              │ • Email send    │         ▼
              └─────────────────┘   [Email Delivery]
                        │                 │
                        ▼                 ▼
                [Status Update]     [Download Link]
```

---

## 8. Security & Rate Limit Considerations

### 8.1 Authentication & Authorization

#### **JWT Implementation**
```python
# app/utils/security.py
class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = 'HS256'):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expires = timedelta(minutes=15)
        self.refresh_token_expires = timedelta(days=30)
    
    def create_access_token(self, user_id: int, permissions: List[str] = None):
        payload = {
            'user_id': user_id,
            'permissions': permissions or [],
            'token_type': 'access',
            'exp': datetime.utcnow() + self.access_token_expires,
            'iat': datetime.utcnow(),
            'jti': str(uuid.uuid4())
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Dict:
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            # Check if token is blacklisted
            if TokenBlacklist.is_blacklisted(payload['jti']):
                raise InvalidTokenError("Token has been revoked")
            return payload
        except jwt.ExpiredSignatureError:
            raise ExpiredTokenError("Token has expired")
        except jwt.InvalidTokenError:
            raise InvalidTokenError("Invalid token")
```

#### **Role-Based Access Control**
```python
# app/middleware/auth_middleware.py
class RBACMiddleware:
    def __init__(self):
        self.permissions = {
            'admin': ['*'],  # All permissions
            'analyst': [
                'influencers:read', 'influencers:write',
                'analytics:read', 'reports:read', 'reports:write'
            ],
            'viewer': ['influencers:read', 'analytics:read', 'reports:read'],
            'guest': ['influencers:read']
        }
    
    def check_permission(self, user_role: str, required_permission: str) -> bool:
        user_permissions = self.permissions.get(user_role, [])
        
        # Admin has all permissions
        if '*' in user_permissions:
            return True
            
        # Check specific permission or wildcard
        resource, action = required_permission.split(':')
        
        return (
            required_permission in user_permissions or
            f"{resource}:*" in user_permissions
        )

# Decorator for endpoint protection
def require_permission(permission: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = get_token_from_request()
            payload = jwt_manager.verify_token(token)
            
            user = User.get(payload['user_id'])
            if not rbac.check_permission(user.role, permission):
                abort(403, description="Insufficient permissions")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### 8.2 Rate Limiting Strategy

#### **Multi-tier Rate Limiting**
```python
# app/utils/rate_limiter.py
from enum import Enum
import redis
from datetime import datetime, timedelta

class RateLimitTier(Enum):
    GUEST = {"requests": 100, "window": 3600}      # 100/hour
    BASIC = {"requests": 1000, "window": 3600}     # 1000/hour  
    PRO = {"requests": 10000, "window": 3600}      # 10k/hour
    ENTERPRISE = {"requests": 100000, "window": 3600}  # 100k/hour

class RateLimiter:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def check_rate_limit(self, user_id: int, endpoint: str, tier: RateLimitTier):
        """Check if user can make request within rate limits"""
        key = f"rate_limit:{user_id}:{endpoint}"
        current_time = int(datetime.utcnow().timestamp())
        window_start = current_time - tier.value["window"]
        
        # Remove expired entries
        self.redis.zremrangebyscore(key, 0, window_start)
        
        # Count current requests in window
        current_requests = self.redis.zcard(key)
        
        if current_requests >= tier.value["requests"]:
            ttl = self.redis.ttl(key)
            raise RateLimitExceeded(
                message=f"Rate limit exceeded. Try again in {ttl} seconds",
                retry_after=ttl
            )
        
        # Add current request
        self.redis.zadd(key, {str(uuid.uuid4()): current_time})
        self.redis.expire(key, tier.value["window"])
        
        return True

# Platform-specific rate limiting
class PlatformRateLimiter:
    def __init__(self):
        self.limits = {
            'instagram': {"requests": 200, "window": 3600},   # Instagram Graph API
            'youtube': {"requests": 10000, "window": 86400},  # YouTube Data API
            'tiktok': {"requests": 1000, "window": 3600},     # TikTok API
            'twitter': {"requests": 300, "window": 900},      # Twitter API v2
        }
    
    async def acquire_slot(self, platform: str, proxy_id: str = None):
        """Acquire rate limit slot for platform API call"""
        limit_key = f"platform_limit:{platform}"
        if proxy_id:
            limit_key += f":{proxy_id}"
        
        # Implement sliding window rate limiting
        # ... implementation details
        
        return RateLimitSlot(platform, proxy_id, expires_at)
```

### 8.3 Data Security & Privacy

#### **Data Encryption**
```python
# app/utils/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class DataEncryption:
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()
        
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data like API keys, personal info"""
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        fernet = Fernet(key)
        
        encrypted_data = fernet.encrypt(data.encode())
        return base64.urlsafe_b64encode(salt + encrypted_data).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        data = base64.urlsafe_b64decode(encrypted_data.encode())
        salt = data[:16]
        encrypted_content = data[16:]
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key))
        fernet = Fernet(key)
        
        return fernet.decrypt(encrypted_content).decode()

# Store encrypted API keys in database
class APIKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(50), nullable=False)
    key_hash = db.Column(db.String(255), nullable=False)  # Encrypted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_key(self, key: str):
        self.key_hash = encryption.encrypt_sensitive_data(key)
    
    def get_key(self) -> str:
        return encryption.decrypt_sensitive_data(self.key_hash)
```

### 8.4 Proxy Management & Security

```python
# app/utils/proxy_manager.py
import aiohttp
import asyncio
from typing import List, Optional
import random

class ProxyManager:
    def __init__(self, proxy_list: List[Dict]):
        self.proxies = proxy_list
        self.active_proxies = []
        self.failed_proxies = set()
        self.health_check_interval = 300  # 5 minutes
        
    async def get_healthy_proxy(self) -> Optional[Dict]:
        """Get a healthy proxy from the pool"""
        if not self.active_proxies:
            await self.refresh_proxy_pool()
        
        if self.active_proxies:
            proxy = random.choice(self.active_proxies)
            return {
                'http': f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}",
                'https': f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            }
        
        return None
    
    async def health_check_proxy(self, proxy: Dict) -> bool:
        """Check if proxy is working"""
        try:
            proxy_url = f"http://{proxy['username']}:{proxy['password']}@{proxy['host']}:{proxy['port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://httpbin.org/ip',
                    proxy=proxy_url,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except:
            return False
    
    async def rotate_proxy(self, failed_proxy: Dict):
        """Mark proxy as failed and get new one"""
        if failed_proxy in self.active_proxies:
            self.active_proxies.remove(failed_proxy)
            self.failed_proxies.add(failed_proxy['host'])
        
        # Try to get replacement proxy
        return await self.get_healthy_proxy()
```

---

## 9. Deployment Architecture

### 9.1 Production Infrastructure

```ascii
┌─────────────────────────────────────────────────────────────┐
│                    Production Architecture                   │
└─────────────────────────────────────────────────────────────┘

                     [CloudFlare CDN]
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Load Balancer                             │
│                   (Nginx + SSL)                             │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ Web Server 1│ │ Web Server 2│ │ Web Server 3│
    │             │ │             │ │             │
    │ Gunicorn    │ │ Gunicorn    │ │ Gunicorn    │
    │ Flask App   │ │ Flask App   │ │ Flask App   │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Cluster                          │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│ PostgreSQL  │ PostgreSQL  │   Redis     │   Redis         │
│   Master    │   Replica   │   Master    │   Replica       │
│             │  (Read-only)│  (Cache)    │  (Backup)       │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   Worker Cluster                            │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│Collection   │Processing   │ Analytics   │ Report          │
│Workers      │Workers      │ Workers     │ Workers         │
│             │             │             │                 │
│ • 20 nodes  │ • 10 nodes  │ • 8 nodes   │ • 4 nodes       │
│ • Proxy     │ • NLP tasks │ • Scoring   │ • PDF/Excel     │
│ • APIs      │ • Cleaning  │ • Trends    │ • Email         │
└─────────────┴─────────────┴─────────────┴─────────────────┘
```

### 9.2 Docker Configuration

#### **Multi-stage Dockerfile for Flask App**
```dockerfile
# Dockerfile.backend
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    redis-tools \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements/production.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as development
COPY requirements/development.txt dev-requirements.txt
RUN pip install --no-cache-dir -r dev-requirements.txt
COPY . .
CMD ["python", "run.py"]

# Production stage
FROM base as production
COPY . .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:create_app()"]
```

#### **Docker Compose for Production**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d
      - ./nginx/ssl:/etc/nginx/ssl
      - static_volume:/app/static
    depends_on:
      - web
    restart: unless-stopped

  web:
    build:
      context: ./backend
      target: production
    ports:
      - "5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/influencer_analytics
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3

  worker-collection:
    build:
      context: ./backend
      target: production
    command: celery -A celery_app.celery worker --loglevel=info --queues=collection --concurrency=10
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@db:5432/influencer_analytics
    depends_on:
      - redis
      - db
    restart: unless-stopped
    deploy:
      replicas: 5

  worker-processing:
    build:
      context: ./backend
      target: production
    command: celery -A celery_app.celery worker --loglevel=info --queues=processing --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped
    deploy:
      replicas: 3

  scheduler:
    build:
      context: ./backend
      target: production
    command: celery -A celery_app.celery beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: influencer_analytics
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./postgres/init:/docker-entrypoint-initdb.d
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      target: production
    ports:
      - "3000:80"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  static_volume:
```

### 9.3 Server Setup Scripts

#### **Automated Ubuntu Server Setup**
```bash
#!/bin/bash
# setup_server.sh

set -e

echo "🚀 Setting up Influencer Analytics Platform..."

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Nginx
sudo apt-get install -y nginx

# Setup SSL with Let's Encrypt
sudo apt-get install -y certbot python3-certbot-nginx

# Configure firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Setup monitoring
sudo apt-get install -y htop iotop ncdu

echo "✅ Server setup complete!"
echo "📝 Next steps:"
echo "   1. Configure domain DNS"
echo "   2. Run SSL setup: sudo certbot --nginx -d yourdomain.com"
echo "   3. Deploy application: docker-compose -f docker-compose.prod.yml up -d"
```

#### **SSL Setup Script**
```bash
#!/bin/bash
# setup_ssl.sh

DOMAIN=${1:-example.com}
EMAIL=${2:-admin@example.com}

echo "🔒 Setting up SSL for $DOMAIN"

# Generate SSL certificate
sudo certbot certonly --nginx \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    -d $DOMAIN \
    -d www.$DOMAIN

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# Configure Nginx
sudo tee /etc/nginx/sites-available/influencer-analytics << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # API
    location /api/ {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/influencer-analytics /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

echo "✅ SSL setup complete for $DOMAIN"
```

---

## 10. Testing Strategy (Unit, Integration, Load)

### 10.1 Unit Testing Framework

```python
# tests/conftest.py
import pytest
from app import create_app, db
from app.models import User, Influencer, Post
from unittest.mock import Mock, patch

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def client(app):
    """Test client"""
    return app.test_client()

@pytest.fixture(scope='function')
def auth_headers(client):
    """Authentication headers for API testing"""
    # Create test user and login
    response = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'TestPass123!'
    })
    token = response.json['access_token']
    return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def sample_influencer():
    """Sample influencer data"""
    return {
        'username': 'test_influencer',
        'platform': 'instagram',
        'follower_count': 50000,
        'verified': True
    }
```

#### **Service Layer Tests**
```python
# tests/test_analytics_service.py
import pytest
from unittest.mock import Mock, patch
from app.services.analytics_service import AnalyticsService
from app.models import Post, Sentiment

class TestAnalyticsService:
    
    @pytest.fixture
    def analytics_service(self):
        return AnalyticsService()
    
    @patch('app.services.analytics_service.SentimentAnalyzer')
    def test_analyze_sentiment(self, mock_analyzer, analytics_service):
        # Arrange
        mock_analyzer.analyze.return_value = {
            'score': 0.8,
            'label': 'positive',
            'confidence': 0.95
        }
        
        post_data = {
            'content': 'Amazing product! Love it!',
            'language': 'en'
        }
        
        # Act
        result = analytics_service.analyze_sentiment(post_data)
        
        # Assert
        assert result['score'] == 0.8
        assert result['label'] == 'positive'
        mock_analyzer.analyze.assert_called_once_with(
            post_data['content'], post_data['language']
        )
    
    def test_compute_influence_score(self, analytics_service):
        # Arrange
        influencer_metrics = {
            'follower_count': 100000,
            'engagement_rate': 0.05,
            'content_quality_score': 0.8,
            'sentiment_score': 0.7
        }
        
        # Act
        score = analytics_service.compute_influence_score(influencer_metrics)
        
        # Assert
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100
        
    @patch('app.services.analytics_service.KeywordExtractor')
    def test_extract_keywords(self, mock_extractor, analytics_service):
        # Arrange
        mock_extractor.extract.return_value = [
            {'keyword': 'technology', 'score': 0.9},
            {'keyword': 'innovation', 'score': 0.8},
            {'keyword': 'digital', 'score': 0.7}
        ]
        
        content = "Technology and innovation in digital transformation"
        
        # Act
        keywords = analytics_service.extract_keywords(content)
        
        # Assert
        assert len(keywords) == 3
        assert keywords[0]['keyword'] == 'technology'
        assert keywords[0]['score'] == 0.9
```

#### **API Integration Tests**
```python
# tests/test_influencer_api.py
import pytest
import json

class TestInfluencerAPI:
    
    def test_get_influencers_success(self, client, auth_headers):
        # Act
        response = client.get('/api/v1/influencers', headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'data' in data
        assert 'pagination' in data
        
    def test_get_influencers_with_filters(self, client, auth_headers):
        # Arrange
        query_params = {
            'platform': 'instagram',
            'min_followers': 10000,
            'verified': 'true'
        }
        
        # Act
        response = client.get(
            '/api/v1/influencers',
            query_string=query_params,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify filtering worked
        for influencer in data['data']:
            assert influencer['platform'] == 'instagram'
            assert influencer['follower_count'] >= 10000
            assert influencer['verified'] is True
            
    def test_create_influencer_success(self, client, auth_headers, sample_influencer):
        # Act
        response = client.post(
            '/api/v1/influencers',
            data=json.dumps(sample_influencer),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['influencer']['username'] == sample_influencer['username']
        
    def test_create_influencer_validation_error(self, client, auth_headers):
        # Arrange - invalid data (missing required fields)
        invalid_data = {'username': 'test'}
        
        # Act
        response = client.post(
            '/api/v1/influencers',
            data=json.dumps(invalid_data),
            content_type='application/json',
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'validation_error' in data['error']
```

### 10.2 Load Testing Strategy

#### **Collection Pipeline Load Test**
```python
# tests/load/test_collection_load.py
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt

class CollectionLoadTest:
    
    def __init__(self, base_url: str, concurrent_requests: int = 100):
        self.base_url = base_url
        self.concurrent_requests = concurrent_requests
        self.results = []
        
    async def simulate_collection_request(self, session, influencer_id: int):
        """Simulate a collection request"""
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/api/v1/influencers/{influencer_id}/collect",
                json={
                    "platforms": ["instagram", "youtube"],
                    "data_types": ["posts", "comments"],
                    "priority": "normal"
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                end_time = time.time()
                
                result = {
                    'influencer_id': influencer_id,
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'success': response.status < 400
                }
                
                if response.status == 200:
                    data = await response.json()
                    result['task_count'] = len(data.get('tasks', []))
                
                return result
                
        except Exception as e:
            return {
                'influencer_id': influencer_id,
                'status_code': 0,
                'response_time': time.time() - start_time,
                'success': False,
                'error': str(e)
            }
    
    async def run_load_test(self, duration_seconds: int = 300):
        """Run load test for specified duration"""
        print(f"🚀 Starting load test: {self.concurrent_requests} concurrent requests for {duration_seconds}s")
        
        end_time = time.time() + duration_seconds
        influencer_counter = 1
        
        async with aiohttp.ClientSession() as session:
            while time.time() < end_time:
                # Create batch of concurrent requests
                tasks = []
                for _ in range(self.concurrent_requests):
                    task = asyncio.create_task(
                        self.simulate_collection_request(session, influencer_counter)
                    )
                    tasks.append(task)
                    influencer_counter += 1
                
                # Execute batch and collect results
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                self.results.extend([r for r in batch_results if isinstance(r, dict)])
                
                # Brief pause between batches
                await asyncio.sleep(0.1)
        
        return self.analyze_results()
    
    def analyze_results(self):
        """Analyze load test results"""
        if not self.results:
            return {"error": "No results collected"}
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        analysis = {
            'total_requests': len(self.results),
            'successful_requests': len(successful_requests),
            'failed_requests': len(failed_requests),
            'success_rate': len(successful_requests) / len(self.results) * 100,
            'avg_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'p95_response_time': self._percentile(response_times, 95) if response_times else 0,
            'p99_response_time': self._percentile(response_times, 99) if response_times else 0,
            'requests_per_second': len(self.results) / (max(r['response_time'] for r in self.results) if self.results else 1)
        }
        
        self.generate_report(analysis)
        return analysis
    
    def _percentile(self, data, percentile):
        """Calculate percentile of data"""
        data.sort()
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        if f == len(data) - 1:
            return data[f]
        return data[f] * (1 - c) + data[f + 1] * c
    
    def generate_report(self, analysis):
        """Generate visual load test report"""
        response_times = [r['response_time'] for r in self.results if r['success']]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Response time histogram
        ax1.hist(response_times, bins=50, alpha=0.7, color='blue')
        ax1.set_title('Response Time Distribution')
        ax1.set_xlabel('Response Time (seconds)')
        ax1.set_ylabel('Frequency')
        
        # Response time over time
        timestamps = range(len(response_times))
        ax2.plot(timestamps, response_times, alpha=0.6)
        ax2.set_title('Response Time Over Time')
        ax2.set_xlabel('Request Number')
        ax2.set_ylabel('Response Time (seconds)')
        
        # Success/Failure pie chart
        success_counts = [analysis['successful_requests'], analysis['failed_requests']]
        ax3.pie(success_counts, labels=['Success', 'Failed'], autopct='%1.1f%%',
                colors=['green', 'red'])
        ax3.set_title('Request Success Rate')
        
        # Status code distribution
        status_codes = {}
        for result in self.results:
            code = result['status_code']
            status_codes[code] = status_codes.get(code, 0) + 1
        
        ax4.bar(status_codes.keys(), status_codes.values())
        ax4.set_title('HTTP Status Code Distribution')
        ax4.set_xlabel('Status Code')
        ax4.set_ylabel('Count')
        
        plt.tight_layout()
        plt.savefig('load_test_report.png', dpi=300, bbox_inches='tight')
        print("📊 Load test report saved as 'load_test_report.png'")

# Run load test
async def main():
    load_test = CollectionLoadTest(
        base_url='http://localhost:5000',
        concurrent_requests=50
    )
    
    results = await load_test.run_load_test(duration_seconds=180)  # 3 minutes
    
    print("\n📈 Load Test Results:")
    print(f"Total Requests: {results['total_requests']}")
    print(f"Success Rate: {results['success_rate']:.2f}%")
    print(f"Average Response Time: {results['avg_response_time']:.3f}s")
    print(f"P95 Response Time: {results['p95_response_time']:.3f}s")
    print(f"P99 Response Time: {results['p99_response_time']:.3f}s")
    print(f"Requests/Second: {results['requests_per_second']:.2f}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 10.3 Database Performance Testing

```python
# tests/performance/test_database_performance.py
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.models import Influencer, Post, Analytics
from sqlalchemy import text

class DatabasePerformanceTest:
    
    def __init__(self, db_session):
        self.db = db_session
        
    def test_bulk_insert_performance(self, record_count: int = 10000):
        """Test bulk insert performance"""
        print(f"🗃️ Testing bulk insert of {record_count} records...")
        
        start_time = time.time()
        
        # Generate test data
        influencers_data = []
        for i in range(record_count):
            influencers_data.append({
                'username': f'test_user_{i}',
                'platform': random.choice(['instagram', 'youtube', 'tiktok']),
                'follower_count': random.randint(1000, 1000000),
                'verified': random.choice([True, False])
            })
        
        # Bulk insert using SQLAlchemy core for performance
        self.db.execute(
            Influencer.__table__.insert(),
            influencers_data
        )
        self.db.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Bulk insert completed: {duration:.2f}s ({record_count/duration:.0f} records/sec)")
        return duration
    
    def test_complex_query_performance(self):
        """Test complex analytics query performance"""
        print("🔍 Testing complex query performance...")
        
        query = text("""
            SELECT 
                i.id,
                i.username,
                i.platform,
                i.follower_count,
                AVG(a.influence_score) as avg_influence_score,
                AVG(a.engagement_rate) as avg_engagement_rate,
                COUNT(p.id) as post_count,
                AVG(s.score) as avg_sentiment
            FROM influencers i
            LEFT JOIN analytics a ON i.id = a.influencer_id
            LEFT JOIN posts p ON i.id = p.influencer_id
            LEFT JOIN sentiments s ON p.id = s.post_id
            WHERE i.follower_count > 10000
            AND a.computed_at > NOW() - INTERVAL '30 days'
            GROUP BY i.id, i.username, i.platform, i.follower_count
            HAVING COUNT(p.id) > 5
            ORDER BY avg_influence_score DESC
            LIMIT 100
        """)
        
        start_time = time.time()
        result = self.db.execute(query).fetchall()
        end_time = time.time()
        
        duration = end_time - start_time
        print(f"✅ Complex query completed: {duration:.3f}s ({len(result)} records)")
        return duration, len(result)
    
    def test_concurrent_read_performance(self, thread_count: int = 10, queries_per_thread: int = 100):
        """Test concurrent read performance"""
        print(f"🔄 Testing concurrent reads: {thread_count} threads, {queries_per_thread} queries each...")
        
        def execute_queries(thread_id):
            thread_results = []
            for i in range(queries_per_thread):
                start_time = time.time()
                
                # Random query type
                if i % 3 == 0:
                    # Get influencer by ID
                    influencer_id = random.randint(1, 1000)
                    result = self.db.query(Influencer).filter_by(id=influencer_id).first()
                elif i % 3 == 1:
                    # Get top influencers
                    result = self.db.query(Influencer).order_by(Influencer.follower_count.desc()).limit(10).all()
                else:
                    # Get analytics data
                    result = self.db.query(Analytics).order_by(Analytics.computed_at.desc()).limit(5).all()
                
                duration = time.time() - start_time
                thread_results.append(duration)
            
            return thread_results
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=thread_count) as executor:
            futures = [executor.submit(execute_queries, i) for i in range(thread_count)]
            all_results = []
            
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        end_time = time.time()
        total_duration = end_time - start_time
        total_queries = thread_count * queries_per_thread
        
        avg_query_time = sum(all_results) / len(all_results)
        
        print(f"✅ Concurrent test completed:")
        print(f"   Total Duration: {total_duration:.2f}s")
        print(f"   Total Queries: {total_queries}")
        print(f"   Queries/Second: {total_queries/total_duration:.0f}")
        print(f"   Average Query Time: {avg_query_time:.4f}s")
        
        return {
            'total_duration': total_duration,
            'queries_per_second': total_queries/total_duration,
            'avg_query_time': avg_query_time
        }
```

---

## 11. Future Expansion Notes

### 11.1 Scalability Considerations

#### **Microservices Migration Path**
```ascii
┌─────────────────────────────────────────────────────────────┐
│                Current Monolith → Microservices             │
└─────────────────────────────────────────────────────────────┘

Phase 1: Extract Services
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Web App   │    │ Collection  │    │ Analytics   │
│ (Core API)  │    │  Service    │    │  Service    │
└─────────────┘    └─────────────┘    └─────────────┘

Phase 2: Add Supporting Services  
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Report      │    │ Notification│    │ User        │
│ Service     │    │  Service    │    │ Service     │
└─────────────┘    └─────────────┘    └─────────────┘

Phase 3: Event-Driven Architecture
         ┌─────────────────┐
         │ Event Bus       │
         │ (Apache Kafka)  │
         └─────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
[Service A]  [Service B]  [Service C]
```

#### **Database Sharding Strategy**
```python
# Future database sharding implementation
class ShardedDatabase:
    def __init__(self, shard_configs):
        self.shards = {}
        for shard_id, config in shard_configs.items():
            self.shards[shard_id] = create_engine(config['url'])
    
    def get_shard_for_influencer(self, influencer_id: int) -> str:
        """Route influencer data to specific shard"""
        # Hash-based sharding
        shard_count = len(self.shards)
        shard_id = f"shard_{influencer_id % shard_count}"
        return shard_id
    
    def get_shard_for_platform(self, platform: str) -> str:
        """Route platform data to specific shard"""
        platform_shards = {
            'instagram': 'shard_0',
            'youtube': 'shard_1', 
            'tiktok': 'shard_2',
            'twitter': 'shard_3'
        }
        return platform_shards.get(platform, 'shard_0')
```

### 11.2 Advanced Analytics Features

#### **Machine Learning Pipeline**
```python
# Future ML pipeline for advanced analytics
class MLPipeline:
    def __init__(self):
        self.models = {
            'engagement_prediction': None,
            'viral_content_detection': None,
            'influencer_authenticity': None,
            'trend_forecasting': None
        }
    
    async def predict_engagement(self, content_features: Dict) -> float:
        """Predict engagement rate for content"""
        # Features: content_type, posting_time, hashtags, sentiment, etc.
        model = await self.load_model('engagement_prediction')
        return model.predict(content_features)
    
    async def detect_viral_potential(self, post_data: Dict) -> Dict:
        """Detect viral potential of content"""
        features = self.extract_viral_features(post_data)
        model = await self.load_model('viral_content_detection')
        
        return {
            'viral_score': model.predict_proba(features)[0][1],
            'key_factors': self.explain_prediction(features),
            'recommendations': self.generate_recommendations(features)
        }
    
    async def assess_influencer_authenticity(self, influencer_id: int) -> Dict:
        """Assess authenticity of influencer using ML"""
        # Analyze follower growth patterns, engagement consistency, etc.
        metrics = await self.collect_authenticity_metrics(influencer_id)
        model = await self.load_model('influencer_authenticity')
        
        return {
            'authenticity_score': model.predict(metrics)[0],
            'red_flags': self.identify_red_flags(metrics),
            'confidence': model.predict_proba(metrics).max()
        }
```

#### **Real-time Trend Detection**
```python
# Future real-time trend detection system
class TrendDetectionEngine:
    def __init__(self, kafka_client, ml_models):
        self.kafka = kafka_client
        self.models = ml_models
        self.trend_cache = {}
        
    async def process_content_stream(self):
        """Process real-time content stream for trend detection"""
        async for message in self.kafka.consume('content_stream'):
            content = message.value
            
            # Extract features
            features = await self.extract_trend_features(content)
            
            # Detect emerging trends
            trends = await self.detect_trends(features)
            
            # Update trend cache
            await self.update_trend_cache(trends)
            
            # Notify subscribers
            await self.notify_trend_updates(trends)
    
    async def detect_trends(self, features: Dict) -> List[Dict]:
        """Detect trending topics using ML"""
        # Use clustering and anomaly detection
        trending_topics = []
        
        for topic, metrics in features.items():
            # Check for sudden spikes in mentions/engagement
            if self.is_trending_spike(metrics):
                trend_data = {
                    'topic': topic,
                    'velocity': self.calculate_trend_velocity(metrics),
                    'sentiment': await self.analyze_trend_sentiment(topic),
                    'influencers': await self.get_trend_influencers(topic),
                    'geographic_spread': await self.analyze_geographic_spread(topic)
                }
                trending_topics.append(trend_data)
        
        return trending_topics
```

### 11.3 Enterprise Features

#### **Multi-tenant Architecture**
```python
# Future multi-tenant support
class TenantManager:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def create_tenant(self, tenant_config: Dict) -> str:
        """Create new tenant with isolated data"""
        tenant_id = self.generate_tenant_id()
        
        # Create tenant-specific database schema
        self.create_tenant_schema(tenant_id)
        
        # Setup tenant configuration
        self.setup_tenant_config(tenant_id, tenant_config)
        
        # Initialize tenant data
        self.initialize_tenant_data(tenant_id)
        
        return tenant_id
    
    def get_tenant_context(self, request) -> str:
        """Extract tenant context from request"""
        # From subdomain, header, or JWT claim
        return request.headers.get('X-Tenant-ID') or \
               self.extract_from_subdomain(request.host)
```

#### **Advanced Security Features**
```python
# Future advanced security implementation
class AdvancedSecurity:
    def __init__(self):
        self.anomaly_detector = AnomalyDetector()
        self.threat_intelligence = ThreatIntelligence()
        
    async def detect_suspicious_activity(self, user_activity: Dict) -> Dict:
        """Detect suspicious user activity"""
        anomalies = await self.anomaly_detector.analyze(user_activity)
        
        risk_score = self.calculate_risk_score(anomalies)
        
        if risk_score > 0.8:
            await self.trigger_security_alert(user_activity, anomalies)
        
        return {
            'risk_score': risk_score,
            'anomalies': anomalies,
            'recommended_actions': self.get_security_recommendations(risk_score)
        }
    
    async def implement_zero_trust_access(self, user: User, resource: str) -> bool:
        """Implement zero-trust access control"""
        # Continuous authentication and authorization
        trust_score = await self.calculate_trust_score(user)
        resource_sensitivity = await self.get_resource_sensitivity(resource)
        
        return trust_score >= resource_sensitivity
```

### 11.4 Integration Roadmap

#### **Third-party Integrations**
```python
# Future integration framework
class IntegrationFramework:
    def __init__(self):
        self.integrations = {}
        
    def register_integration(self, name: str, integration_class):
        """Register new integration"""
        self.integrations[name] = integration_class
        
    async def add_crm_integration(self):
        """Integrate with CRM systems (HubSpot, Salesforce)"""
        # Sync influencer data with CRM contacts
        # Track campaign ROI and attribution
        pass
        
    async def add_ecommerce_integration(self):
        """Integrate with e-commerce platforms (Shopify, WooCommerce)"""
        # Track influencer-driven sales
        # Calculate conversion rates and ROI
        pass
        
    async def add_advertising_integration(self):
        """Integrate with ad platforms (Facebook Ads, Google Ads)"""
        # Sync audience data
        # Optimize ad targeting based on influencer insights
        pass
```

This comprehensive SRS provides a complete roadmap for building a scalable, secure, and feature-rich influencer analytics platform. The modular architecture allows for incremental development and easy expansion of capabilities as requirements evolve.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "Design comprehensive system architecture and database schema", "status": "completed", "activeForm": "Designing comprehensive system architecture and database schema"}, {"content": "Create influencer data collection module with API integrations", "status": "pending", "activeForm": "Creating influencer data collection module with API integrations"}, {"content": "Build data processing and analytics pipeline", "status": "pending", "activeForm": "Building data processing and analytics pipeline"}, {"content": "Implement dashboard with drag-drop widgets", "status": "pending", "activeForm": "Implementing dashboard with drag-drop widgets"}, {"content": "Create report generation system", "status": "pending", "activeForm": "Creating report generation system"}, {"content": "Set up payment integration and subscription management", "status": "pending", "activeForm": "Setting up payment integration and subscription management"}, {"content": "Design deployment architecture and security", "status": "pending", "activeForm": "Designing deployment architecture and security"}, {"content": "Create comprehensive documentation and testing strategy", "status": "completed", "activeForm": "Creating comprehensive documentation and testing strategy"}]