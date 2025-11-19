#!/bin/bash

# Backup script for Influencer Analytics Platform
# Supports both database and file backups with encryption

set -e

# Configuration
PROJECT_NAME="influencer-analytics"
BACKUP_DIR="/opt/backups/$PROJECT_NAME"
LOG_FILE="/var/log/$PROJECT_NAME-backup.log"
ENCRYPTION_KEY_FILE="/opt/ssl/$PROJECT_NAME/backup.key"

# Load environment variables
if [[ -f ".env" ]]; then
    export $(cat .env | grep -v ^# | xargs)
fi

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

info() {
    echo -e "${BLUE}[INFO] $1${NC}" | tee -a "$LOG_FILE"
}

# Create backup directories
setup_backup_dirs() {
    sudo mkdir -p "$BACKUP_DIR/database"
    sudo mkdir -p "$BACKUP_DIR/files"
    sudo mkdir -p "$BACKUP_DIR/configs"
    sudo chown -R $USER:$USER "$BACKUP_DIR"
}

# Generate encryption key if not exists
setup_encryption() {
    if [[ ! -f "$ENCRYPTION_KEY_FILE" ]]; then
        info "Generating backup encryption key..."
        sudo mkdir -p "$(dirname $ENCRYPTION_KEY_FILE)"
        openssl rand -base64 32 | sudo tee "$ENCRYPTION_KEY_FILE" > /dev/null
        sudo chmod 600 "$ENCRYPTION_KEY_FILE"
        sudo chown $USER:$USER "$ENCRYPTION_KEY_FILE"
        success "Encryption key generated"
    fi
}

# Database backup
backup_database() {
    info "Starting database backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/database/db_backup_$TIMESTAMP.sql"
    
    # Check if database is running
    if ! docker-compose ps postgres | grep -q "Up"; then
        error "PostgreSQL container is not running"
        return 1
    fi
    
    # Create database dump
    info "Creating database dump..."
    docker-compose exec -T postgres pg_dump \
        -U "${POSTGRES_USER:-video_user}" \
        -h localhost \
        -p 5432 \
        --verbose \
        --clean \
        --no-owner \
        --no-privileges \
        "${POSTGRES_DB:-video_tracking_db}" > "$BACKUP_FILE"
    
    # Encrypt and compress
    info "Encrypting and compressing backup..."
    openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" \
        -out "${BACKUP_FILE}.enc" \
        -pass file:"$ENCRYPTION_KEY_FILE"
    
    gzip "${BACKUP_FILE}.enc"
    rm "$BACKUP_FILE"
    
    FINAL_BACKUP="${BACKUP_FILE}.enc.gz"
    BACKUP_SIZE=$(du -h "$FINAL_BACKUP" | cut -f1)
    
    success "Database backup completed: $FINAL_BACKUP ($BACKUP_SIZE)"
    
    # Cleanup old backups (keep last 7 days)
    find "$BACKUP_DIR/database" -name "db_backup_*.sql.enc.gz" -type f -mtime +7 -delete
    
    echo "$FINAL_BACKUP"
}

# Redis backup
backup_redis() {
    info "Starting Redis backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/database/redis_backup_$TIMESTAMP.rdb"
    
    # Check if Redis is running
    if ! docker-compose ps redis | grep -q "Up"; then
        error "Redis container is not running"
        return 1
    fi
    
    # Save Redis data
    docker-compose exec -T redis redis-cli --rdb /data/dump.rdb BGSAVE
    sleep 5  # Wait for background save to complete
    
    # Copy Redis dump
    docker-compose exec -T redis cat /data/dump.rdb > "$BACKUP_FILE"
    
    # Encrypt and compress
    openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" \
        -out "${BACKUP_FILE}.enc" \
        -pass file:"$ENCRYPTION_KEY_FILE"
    
    gzip "${BACKUP_FILE}.enc"
    rm "$BACKUP_FILE"
    
    FINAL_BACKUP="${BACKUP_FILE}.enc.gz"
    BACKUP_SIZE=$(du -h "$FINAL_BACKUP" | cut -f1)
    
    success "Redis backup completed: $FINAL_BACKUP ($BACKUP_SIZE)"
    
    # Cleanup old backups
    find "$BACKUP_DIR/database" -name "redis_backup_*.rdb.enc.gz" -type f -mtime +7 -delete
    
    echo "$FINAL_BACKUP"
}

# Configuration files backup
backup_configs() {
    info "Starting configuration backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    CONFIG_DIR="$BACKUP_DIR/configs/config_backup_$TIMESTAMP"
    
    mkdir -p "$CONFIG_DIR"
    
    # Backup important config files
    files_to_backup=(
        ".env"
        "docker-compose.yml"
        "frontend/nginx.conf"
        "backend/Dockerfile"
        "frontend/Dockerfile"
        "scripts/deploy.sh"
        "scripts/backup.sh"
    )
    
    for file in "${files_to_backup[@]}"; do
        if [[ -f "$file" ]]; then
            mkdir -p "$CONFIG_DIR/$(dirname $file)"
            cp "$file" "$CONFIG_DIR/$file"
            info "Backed up: $file"
        fi
    done
    
    # Create archive
    tar -czf "${CONFIG_DIR}.tar.gz" -C "$BACKUP_DIR/configs" "$(basename $CONFIG_DIR)"
    rm -rf "$CONFIG_DIR"
    
    # Encrypt
    openssl enc -aes-256-cbc -salt -in "${CONFIG_DIR}.tar.gz" \
        -out "${CONFIG_DIR}.tar.gz.enc" \
        -pass file:"$ENCRYPTION_KEY_FILE"
    
    rm "${CONFIG_DIR}.tar.gz"
    
    BACKUP_SIZE=$(du -h "${CONFIG_DIR}.tar.gz.enc" | cut -f1)
    success "Configuration backup completed: ${CONFIG_DIR}.tar.gz.enc ($BACKUP_SIZE)"
    
    # Cleanup old backups
    find "$BACKUP_DIR/configs" -name "config_backup_*.tar.gz.enc" -type f -mtime +30 -delete
}

# Application files backup
backup_files() {
    info "Starting application files backup..."
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/files/app_backup_$TIMESTAMP.tar.gz"
    
    # Files to exclude
    exclude_patterns=(
        "--exclude=.git"
        "--exclude=node_modules"
        "--exclude=__pycache__"
        "--exclude=*.pyc"
        "--exclude=.env"
        "--exclude=logs"
        "--exclude=.DS_Store"
        "--exclude=*.log"
        "--exclude=build"
        "--exclude=dist"
    )
    
    # Create archive
    tar -czf "$BACKUP_FILE" "${exclude_patterns[@]}" \
        --exclude="$BACKUP_DIR" \
        -C .. "$(basename $(pwd))"
    
    # Encrypt
    openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" \
        -out "${BACKUP_FILE}.enc" \
        -pass file:"$ENCRYPTION_KEY_FILE"
    
    rm "$BACKUP_FILE"
    
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}.enc" | cut -f1)
    success "Application files backup completed: ${BACKUP_FILE}.enc ($BACKUP_SIZE)"
    
    # Cleanup old backups (keep last 3)
    find "$BACKUP_DIR/files" -name "app_backup_*.tar.gz.enc" -type f | \
        sort -r | tail -n +4 | xargs rm -f
}

# Upload to S3 (if configured)
upload_to_s3() {
    if [[ -z "$AWS_ACCESS_KEY_ID" ]] || [[ -z "$BACKUP_S3_BUCKET" ]]; then
        info "S3 backup not configured, skipping cloud upload"
        return 0
    fi
    
    info "Uploading backups to S3..."
    
    local backup_file="$1"
    local s3_path="s3://$BACKUP_S3_BUCKET/$(basename $(dirname $backup_file))/$(basename $backup_file)"
    
    if command -v aws &> /dev/null; then
        aws s3 cp "$backup_file" "$s3_path" --storage-class STANDARD_IA
        success "Uploaded to S3: $s3_path"
    else
        error "AWS CLI not installed, skipping S3 upload"
    fi
}

# Restore database
restore_database() {
    local backup_file="$1"
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    info "Restoring database from: $backup_file"
    
    # Decrypt and decompress
    temp_file="/tmp/restore_$(date +%s).sql"
    
    if [[ "$backup_file" == *.enc.gz ]]; then
        gunzip -c "$backup_file" | openssl enc -aes-256-cbc -d -pass file:"$ENCRYPTION_KEY_FILE" > "$temp_file"
    elif [[ "$backup_file" == *.enc ]]; then
        openssl enc -aes-256-cbc -d -in "$backup_file" -pass file:"$ENCRYPTION_KEY_FILE" > "$temp_file"
    else
        cp "$backup_file" "$temp_file"
    fi
    
    # Restore database
    docker-compose exec -T postgres psql \
        -U "${POSTGRES_USER:-video_user}" \
        -d "${POSTGRES_DB:-video_tracking_db}" < "$temp_file"
    
    rm "$temp_file"
    success "Database restored successfully"
}

# List available backups
list_backups() {
    info "Available backups:"
    echo ""
    
    echo "Database backups:"
    find "$BACKUP_DIR/database" -name "db_backup_*.sql.enc.gz" -type f -printf "%T@ %Tc %p\n" | sort -n | cut -d' ' -f2-
    
    echo ""
    echo "Redis backups:"
    find "$BACKUP_DIR/database" -name "redis_backup_*.rdb.enc.gz" -type f -printf "%T@ %Tc %p\n" | sort -n | cut -d' ' -f2-
    
    echo ""
    echo "Configuration backups:"
    find "$BACKUP_DIR/configs" -name "config_backup_*.tar.gz.enc" -type f -printf "%T@ %Tc %p\n" | sort -n | cut -d' ' -f2-
    
    echo ""
    echo "Application backups:"
    find "$BACKUP_DIR/files" -name "app_backup_*.tar.gz.enc" -type f -printf "%T@ %Tc %p\n" | sort -n | cut -d' ' -f2-
}

# Full backup
full_backup() {
    log "Starting full backup process..."
    
    setup_backup_dirs
    setup_encryption
    
    # Perform all backups
    db_backup=$(backup_database)
    redis_backup=$(backup_redis)
    backup_configs
    backup_files
    
    # Upload to S3 if configured
    if [[ -n "$db_backup" ]]; then
        upload_to_s3 "$db_backup"
    fi
    
    success "Full backup process completed"
    
    # Display summary
    echo ""
    info "Backup Summary:"
    info "Database: $(find "$BACKUP_DIR/database" -name "db_backup_*.sql.enc.gz" -type f | wc -l) backups"
    info "Redis: $(find "$BACKUP_DIR/database" -name "redis_backup_*.rdb.enc.gz" -type f | wc -l) backups"
    info "Configs: $(find "$BACKUP_DIR/configs" -name "config_backup_*.tar.gz.enc" -type f | wc -l) backups"
    info "Files: $(find "$BACKUP_DIR/files" -name "app_backup_*.tar.gz.enc" -type f | wc -l) backups"
    
    total_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    info "Total backup size: $total_size"
}

# Show usage
show_usage() {
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --full             Perform full backup (default)"
    echo "  --database         Backup database only"
    echo "  --redis           Backup Redis only"
    echo "  --configs         Backup configurations only"
    echo "  --files           Backup application files only"
    echo "  --list            List available backups"
    echo "  --restore <file>  Restore database from backup file"
    echo "  --help, -h        Show this help message"
    echo ""
}

# Main function
main() {
    case "${1:-full}" in
        "--full"|"full")
            full_backup
            ;;
        "--database"|"database")
            setup_backup_dirs
            setup_encryption
            backup_database
            ;;
        "--redis"|"redis")
            setup_backup_dirs
            setup_encryption
            backup_redis
            ;;
        "--configs"|"configs")
            setup_backup_dirs
            setup_encryption
            backup_configs
            ;;
        "--files"|"files")
            setup_backup_dirs
            setup_encryption
            backup_files
            ;;
        "--list"|"list")
            list_backups
            ;;
        "--restore"|"restore")
            if [[ -z "$2" ]]; then
                error "Please specify backup file to restore"
                show_usage
                exit 1
            fi
            setup_encryption
            restore_database "$2"
            ;;
        "--help"|"-h"|"help")
            show_usage
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Check if we're in the right directory
if [[ ! -f "docker-compose.yml" ]]; then
    error "docker-compose.yml not found. Please run this script from the project root directory."
    exit 1
fi

# Run main function
main "$@"