#!/bin/bash

# Production deployment script for Influencer Analytics Platform
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="influencer-analytics"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
LOG_FILE="/var/log/$PROJECT_NAME-deploy.log"

# Functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        error "This script should not be run as root for security reasons"
        error "Please run as a regular user with sudo privileges"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    info "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if user is in docker group
    if ! groups $USER | grep -q docker; then
        error "User $USER is not in the docker group."
        error "Run: sudo usermod -aG docker $USER && newgrp docker"
        exit 1
    fi
    
    success "System requirements check passed"
}

# Setup environment
setup_environment() {
    info "Setting up environment..."
    
    # Create necessary directories
    sudo mkdir -p /opt/logs/$PROJECT_NAME
    sudo mkdir -p $BACKUP_DIR
    sudo mkdir -p /opt/ssl/$PROJECT_NAME
    
    # Set permissions
    sudo chown -R $USER:$USER /opt/logs/$PROJECT_NAME
    sudo chown -R $USER:$USER $BACKUP_DIR
    
    # Create log file
    sudo touch $LOG_FILE
    sudo chown $USER:$USER $LOG_FILE
    
    success "Environment setup completed"
}

# Setup SSL certificates
setup_ssl() {
    info "Setting up SSL certificates..."
    
    DOMAIN=${DOMAIN_NAME:-"localhost"}
    SSL_DIR="/opt/ssl/$PROJECT_NAME"
    
    if [[ "$DOMAIN" == "localhost" ]]; then
        warning "Using localhost - generating self-signed certificate"
        
        # Generate self-signed certificate for development
        sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout $SSL_DIR/private.key \
            -out $SSL_DIR/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
    else
        info "For production, please set up Let's Encrypt certificates:"
        info "1. sudo apt install certbot"
        info "2. sudo certbot certonly --standalone -d $DOMAIN"
        info "3. Copy certificates to $SSL_DIR/"
        
        # Check if certificates exist
        if [[ ! -f "$SSL_DIR/cert.pem" ]] || [[ ! -f "$SSL_DIR/private.key" ]]; then
            warning "SSL certificates not found. Creating self-signed certificate..."
            sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout $SSL_DIR/private.key \
                -out $SSL_DIR/cert.pem \
                -subj "/C=US/ST=State/L=City/O=Organization/CN=$DOMAIN"
        fi
    fi
    
    # Set proper permissions
    sudo chmod 600 $SSL_DIR/private.key
    sudo chmod 644 $SSL_DIR/cert.pem
    
    success "SSL certificates configured"
}

# Create environment file
create_env_file() {
    info "Creating environment file..."
    
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            cp .env.example .env
            info "Created .env from .env.example"
            warning "Please update .env with your production values before continuing"
            warning "Pay special attention to:"
            warning "- SECRET_KEY and JWT_SECRET_KEY (use random strings)"
            warning "- Database passwords"
            warning "- Redis password"
            warning "- Stripe API keys"
            warning "- Email configuration"
            
            echo "Press Enter after updating .env file..."
            read
        else
            error ".env.example not found. Please create .env file manually"
            exit 1
        fi
    else
        info ".env file already exists"
    fi
    
    success "Environment file ready"
}

# Database backup
backup_database() {
    info "Creating database backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
    # Only backup if database exists and is running
    if docker-compose ps postgres | grep -q "Up"; then
        docker-compose exec -T postgres pg_dump -U video_user video_tracking_db > "$BACKUP_FILE"
        gzip "$BACKUP_FILE"
        success "Database backup created: ${BACKUP_FILE}.gz"
        
        # Keep only last 7 backups
        find $BACKUP_DIR -name "db_backup_*.sql.gz" -type f -mtime +7 -delete
    else
        info "Database not running, skipping backup"
    fi
}

# Build and deploy
deploy() {
    info "Starting deployment..."
    
    # Pull latest changes (if this is a git deployment)
    if [[ -d ".git" ]]; then
        info "Pulling latest changes..."
        git pull origin main
    fi
    
    # Build images
    info "Building Docker images..."
    docker-compose build --no-cache
    
    # Stop existing containers
    info "Stopping existing containers..."
    docker-compose down
    
    # Start new containers
    info "Starting new containers..."
    docker-compose up -d
    
    # Wait for services to be ready
    info "Waiting for services to be ready..."
    sleep 30
    
    # Initialize database
    info "Initializing database..."
    docker-compose exec backend python scripts/init_db.py
    
    # Run any pending migrations
    info "Running database migrations..."
    docker-compose exec backend flask db upgrade
    
    success "Deployment completed"
}

# Health check
health_check() {
    info "Performing health checks..."
    
    # Check if all services are running
    services=("postgres" "redis" "backend" "frontend" "celery-worker" "flower")
    
    for service in "${services[@]}"; do
        if docker-compose ps $service | grep -q "Up"; then
            success "$service is running"
        else
            error "$service is not running"
            docker-compose logs $service
        fi
    done
    
    # Check API health
    info "Checking API health..."
    sleep 10
    
    if curl -f -s http://localhost:5000/api/health > /dev/null; then
        success "API health check passed"
    else
        error "API health check failed"
        docker-compose logs backend
    fi
    
    # Check frontend
    info "Checking frontend..."
    if curl -f -s http://localhost:80 > /dev/null; then
        success "Frontend health check passed"
    else
        error "Frontend health check failed"
        docker-compose logs frontend
    fi
    
    success "Health checks completed"
}

# Setup monitoring
setup_monitoring() {
    info "Setting up monitoring..."
    
    # Create monitoring directories
    sudo mkdir -p /opt/monitoring/$PROJECT_NAME
    
    # Setup log rotation
    sudo tee /etc/logrotate.d/$PROJECT_NAME << EOF
/var/log/$PROJECT_NAME-*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 $USER $USER
}
EOF
    
    # Setup basic monitoring script
    cat > /opt/monitoring/$PROJECT_NAME/check_services.sh << 'EOF'
#!/bin/bash
# Basic service monitoring script

PROJECT_DIR="/home/$USER/Project/Video-Tracking"
cd "$PROJECT_DIR"

# Check services
services=("postgres" "redis" "backend" "frontend" "celery-worker")
all_healthy=true

for service in "${services[@]}"; do
    if ! docker-compose ps $service | grep -q "Up"; then
        echo "$(date): $service is down" >> /var/log/influencer-analytics-monitor.log
        all_healthy=false
    fi
done

# Check API
if ! curl -f -s http://localhost:5000/api/health > /dev/null; then
    echo "$(date): API health check failed" >> /var/log/influencer-analytics-monitor.log
    all_healthy=false
fi

if $all_healthy; then
    echo "$(date): All services healthy" >> /var/log/influencer-analytics-monitor.log
fi
EOF
    
    chmod +x /opt/monitoring/$PROJECT_NAME/check_services.sh
    
    # Setup cron job for monitoring
    (crontab -l 2>/dev/null; echo "*/5 * * * * /opt/monitoring/$PROJECT_NAME/check_services.sh") | crontab -
    
    success "Monitoring setup completed"
}

# Main deployment function
main() {
    log "Starting deployment process for $PROJECT_NAME"
    
    # Check if we're in the right directory
    if [[ ! -f "docker-compose.yml" ]]; then
        error "docker-compose.yml not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Run deployment steps
    check_root
    check_requirements
    setup_environment
    create_env_file
    setup_ssl
    
    # Ask for confirmation before proceeding
    echo ""
    warning "Ready to deploy. This will:"
    warning "- Build and restart all containers"
    warning "- Initialize/migrate the database"
    warning "- Setup monitoring"
    echo ""
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Deployment cancelled"
        exit 0
    fi
    
    backup_database
    deploy
    health_check
    setup_monitoring
    
    success "Deployment completed successfully!"
    
    echo ""
    info "🎉 Your Influencer Analytics Platform is now running!"
    info "📊 Frontend: http://localhost (or your domain)"
    info "🔧 API: http://localhost:5000/api"
    info "🌸 Flower (Celery Monitor): http://localhost:5555"
    info "📋 PgAdmin: http://localhost:5050"
    echo ""
    info "📝 Next steps:"
    info "1. Access the admin panel and change default passwords"
    info "2. Configure your payment settings in the admin panel"
    info "3. Set up your data collection sources"
    info "4. Configure email settings for notifications"
    info "5. Set up proper domain and SSL certificates for production"
    echo ""
    warning "🔒 Security reminders:"
    warning "- Change all default passwords"
    warning "- Configure firewall rules"
    warning "- Set up proper SSL certificates"
    warning "- Configure backup strategies"
    warning "- Review and update environment variables"
}

# Show usage if help is requested
if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --backup-only  Only create database backup"
    echo "  --health-check Only perform health checks"
    echo ""
    echo "Environment variables:"
    echo "  DOMAIN_NAME    Domain name for SSL certificates (default: localhost)"
    echo ""
    exit 0
fi

# Handle special modes
if [[ "$1" == "--backup-only" ]]; then
    backup_database
    exit 0
elif [[ "$1" == "--health-check" ]]; then
    health_check
    exit 0
fi

# Run main deployment
main