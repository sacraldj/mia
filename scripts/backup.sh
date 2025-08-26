#!/bin/bash
# Mi AI Service - Backup Script
# =============================

echo "💾 Mi AI Service - Backup"
echo "=========================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'  
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/backup.log
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: $1" >> logs/backup.log
}

error() {
    echo -e "${RED}❌ $1${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >> logs/backup.log
}

# Ensure we're in the right directory
cd "$(dirname "$0")/.." || exit 1

# Create backup directories
mkdir -p backups/{configs,images,logs,data}
mkdir -p logs

BACKUP_DATE=$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR="backups"

log "💾 Starting backup process..."
log "📅 Backup timestamp: $BACKUP_DATE"

# Backup 1: Configuration files
log "⚙️ Backing up configuration files..."
cp config.json "$BACKUP_DIR/configs/config_$BACKUP_DATE.json" 2>/dev/null || warn "config.json not found"
cp requirements.txt "$BACKUP_DIR/configs/requirements_$BACKUP_DATE.txt" 2>/dev/null || warn "requirements.txt not found"

if [ -f ".env" ]; then
    # Backup .env but remove sensitive data
    sed 's/=.*/=***REDACTED***/g' .env > "$BACKUP_DIR/configs/env_template_$BACKUP_DATE.txt"
    log "✅ Configuration files backed up (credentials redacted)"
else
    warn ".env file not found"
fi

# Backup 2: Generated images (keep last 20)
log "🖼️ Backing up recent generated images..."
IMAGE_COUNT=0
if [ -d "/tmp/generated_images" ]; then
    # Get last 20 images by modification time
    find /tmp/generated_images -name "*.png" -type f -printf '%T@ %p\n' 2>/dev/null | \
    sort -nr | head -20 | cut -d' ' -f2- | while read -r img; do
        if [ -f "$img" ]; then
            BASENAME=$(basename "$img")
            cp "$img" "$BACKUP_DIR/images/" 2>/dev/null
            ((IMAGE_COUNT++))
        fi
    done
    log "✅ Backed up recent images"
else
    warn "Generated images directory not found"
fi

# Backup 3: Application logs (last 1000 lines of each)
log "📋 Backing up application logs..."
if [ -f "logs/service.log" ]; then
    tail -1000 "logs/service.log" > "$BACKUP_DIR/logs/service_$BACKUP_DATE.log"
fi
if [ -f "logs/sync.log" ]; then
    tail -1000 "logs/sync.log" > "$BACKUP_DIR/logs/sync_$BACKUP_DATE.log"
fi
if [ -f "logs/backup.log" ]; then
    tail -1000 "logs/backup.log" > "$BACKUP_DIR/logs/backup_$BACKUP_DATE.log"  
fi
log "✅ Application logs backed up"

# Backup 4: Service statistics and metadata
log "📊 Generating service statistics..."
cat > "$BACKUP_DIR/data/stats_$BACKUP_DATE.json" << EOF
{
    "backup_timestamp": "$BACKUP_DATE",
    "backup_date": "$(date)",
    "git_info": {
        "branch": "$(git branch --show-current 2>/dev/null || echo 'unknown')",
        "last_commit": "$(git log -1 --format='%h - %s' 2>/dev/null || echo 'No commits')",
        "commit_count": $(git rev-list --count HEAD 2>/dev/null || echo 0)
    },
    "service_info": {
        "version": "2.0.0",
        "python_version": "$(python3 --version 2>/dev/null || echo 'unknown')",
        "disk_usage": "$(df -h . | tail -1 | awk '{print $3 "/" $2 " (" $5 ")"}')",
        "uptime": "$(uptime -p 2>/dev/null || echo 'unknown')"
    },
    "file_counts": {
        "config_backups": $(ls -1 $BACKUP_DIR/configs/ 2>/dev/null | wc -l),
        "image_backups": $(ls -1 $BACKUP_DIR/images/ 2>/dev/null | wc -l),
        "log_backups": $(ls -1 $BACKUP_DIR/logs/ 2>/dev/null | wc -l)
    }
}
EOF

# Backup 5: Current service status
log "🏥 Capturing service status..."
if command -v curl >/dev/null 2>&1; then
    curl -s http://localhost:8000/health > "$BACKUP_DIR/data/health_$BACKUP_DATE.json" 2>/dev/null || \
        echo '{"error": "Service not responding"}' > "$BACKUP_DIR/data/health_$BACKUP_DATE.json"
    
    curl -s http://localhost:8000/stats > "$BACKUP_DIR/data/service_stats_$BACKUP_DATE.json" 2>/dev/null || \
        echo '{"error": "Stats not available"}' > "$BACKUP_DIR/data/service_stats_$BACKUP_DATE.json"
else
    warn "curl not available for health check"
fi

# Cleanup: Remove old backups (keep last 10 of each type)
log "🧹 Cleaning up old backups..."

cleanup_old_files() {
    local dir="$1"
    local keep="$2"
    
    if [ -d "$dir" ]; then
        local count=$(ls -1 "$dir" | wc -l)
        if [ "$count" -gt "$keep" ]; then
            ls -1t "$dir" | tail -n +$((keep + 1)) | while read -r file; do
                rm -f "$dir/$file" 2>/dev/null
            done
            log "🗑️ Cleaned up old files in $dir"
        fi
    fi
}

cleanup_old_files "$BACKUP_DIR/configs" 10
cleanup_old_files "$BACKUP_DIR/images" 50
cleanup_old_files "$BACKUP_DIR/logs" 5
cleanup_old_files "$BACKUP_DIR/data" 10

# Create backup summary
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
CONFIG_COUNT=$(ls -1 "$BACKUP_DIR/configs/" 2>/dev/null | wc -l)
IMAGE_COUNT=$(ls -1 "$BACKUP_DIR/images/" 2>/dev/null | wc -l)
LOG_COUNT=$(ls -1 "$BACKUP_DIR/logs/" 2>/dev/null | wc -l)

cat > "$BACKUP_DIR/BACKUP_SUMMARY.txt" << EOF
Mi AI Service - Backup Summary
==============================
Date: $(date)
Backup ID: $BACKUP_DATE

Contents:
- Configuration files: $CONFIG_COUNT
- Image backups: $IMAGE_COUNT  
- Log files: $LOG_COUNT
- Total size: $TOTAL_SIZE

Git Information:
- Branch: $(git branch --show-current 2>/dev/null || echo 'unknown')
- Last commit: $(git log -1 --format='%h - %s' 2>/dev/null || echo 'No commits')

System Information:
- Python: $(python3 --version 2>/dev/null || echo 'unknown')
- Disk usage: $(df -h . | tail -1 | awk '{print $5 " used"}')
- Memory: $(free -h | head -2 | tail -1 | awk '{print $3 "/" $2 " used"}' 2>/dev/null || echo 'unknown')

Backup completed successfully!
EOF

# Add to Git for version control
log "📤 Adding backup to Git..."
git add backups/
if git diff --cached --quiet; then
    log "📝 No new backup data to commit"
else
    git commit -m "Automatic backup: $BACKUP_DATE" 2>/dev/null || warn "Git commit failed"
    log "✅ Backup committed to Git"
fi

# Try to push to GitHub
if git push origin main 2>/dev/null; then
    log "☁️ Backup pushed to GitHub"
else
    warn "Could not push backup to GitHub (check authentication)"
fi

# Final summary
echo ""
log "🎉 BACKUP COMPLETED!"
echo "===================="
echo ""
echo -e "${BLUE}📊 Backup Summary:${NC}"
echo "• Backup ID: $BACKUP_DATE"
echo "• Total size: $TOTAL_SIZE"
echo "• Config files: $CONFIG_COUNT"
echo "• Images: $IMAGE_COUNT"
echo "• Logs: $LOG_COUNT"
echo ""
echo -e "${BLUE}📁 Backup location:${NC}"
echo "• Local: $PWD/$BACKUP_DIR/"
echo "• GitHub: https://github.com/sacraldj/mia/tree/main/backups"
echo ""
echo -e "${GREEN}✅ All data safely backed up!${NC}"
