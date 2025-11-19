# Video Tracking Project

A full-stack "Hello World" application using React frontend, Flask backend, Celery task queue, and Redis.

## Architecture

- **Frontend**: React with TypeScript
- **Backend**: Flask (Python)
- **Task Queue**: Celery
- **Message Broker**: Redis
- **Containerization**: Docker & Docker Compose

## Features

- Synchronous API endpoint (`/api/hello`)
- Asynchronous task processing with Celery
- Real-time task status polling
- Dockerized development environment

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

#### Backend
```bash
cd backend
pip install -r requirements.txt

# Start Redis (required)
redis-server

# Start Flask app
python app.py

# Start Celery worker (in another terminal)
celery -A app.celery worker --loglevel=info
```

#### Frontend
```bash
cd frontend
npm install
npm start
```

## API Endpoints

- `GET /api/hello` - Simple hello world message
- `POST /api/hello-async/<name>` - Start async task
- `GET /api/task/<task_id>` - Check task status

## Project Structure

```
├── backend/
│   ├── app.py              # Flask application
│   ├── celery_worker.py    # Celery worker entry point
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Backend container config
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Main React component
│   │   └── App.css        # Styling
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Frontend container config
├── docker-compose.yml     # Multi-service orchestration
└── README.md             # This file
```

## Development Notes

- Frontend runs on port 3001
- Backend runs on port 5001
- Redis runs on port 6379
- CORS is configured for localhost:3001
- All services auto-reload on file changes in development mode