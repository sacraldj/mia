#!/bin/bash
# Mi AI Service - Git Sync Script
# ===============================

echo "🔄 Mi AI Service - Git Sync"
echo "============================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> logs/sync.log
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - WARNING: $1" >> logs/sync.log
}

error() {
    echo -e "${RED}❌ $1${NC}"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" >> logs/sync.log
}

# Ensure we're in the right directory
cd "$(dirname "$0")/.." || exit 1

# Create logs directory
mkdir -p logs

log "🔄 Starting Git synchronization..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    error "Git repository not initialized. Run quick-setup.sh first."
    exit 1
fi

# Stash any uncommitted changes
log "💾 Stashing local changes..."
git stash push -u -m "Auto-stash before sync $(date)" 2>/dev/null

# Fetch latest changes
log "📥 Fetching changes from GitHub..."
if git fetch origin main 2>/dev/null; then
    log "✅ Fetch successful"
else
    warn "Fetch failed - remote may not exist yet"
fi

# Check for remote changes
if git diff HEAD origin/main --quiet 2>/dev/null; then
    log "📊 No remote changes detected"
    REMOTE_CHANGES=false
else
    log "📈 Remote changes detected, pulling..."
    REMOTE_CHANGES=true
fi

# Pull changes if they exist
if [ "$REMOTE_CHANGES" = true ]; then
    if git pull origin main 2>/dev/null; then
        log "✅ Pull successful"
        
        # Restart service if main.py or config.json changed
        if git diff HEAD~1 --name-only | grep -E "(main\.py|config\.json|requirements\.txt)" > /dev/null; then
            log "🔄 Critical files changed, restarting service..."
            ./scripts/restart.sh
        fi
    else
        warn "Pull failed, attempting merge resolution..."
        git merge --abort 2>/dev/null
        
        # Restore from stash and try again
        git stash pop 2>/dev/null
        warn "Manual intervention may be required"
    fi
fi

# Add all new changes
log "📋 Adding local changes..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    log "📝 No local changes to commit"
    LOCAL_CHANGES=false
else
    log "📤 Local changes detected, committing..."
    LOCAL_CHANGES=true
fi

# Commit changes if they exist
if [ "$LOCAL_CHANGES" = true ]; then
    # Generate commit message based on changes
    CHANGED_FILES=$(git diff --cached --name-only | wc -l)
    COMMIT_MSG="Auto-sync: Updated $CHANGED_FILES files on $(date '+%Y-%m-%d %H:%M:%S')"
    
    if git commit -m "$COMMIT_MSG" 2>/dev/null; then
        log "✅ Commit successful: $COMMIT_MSG"
        
        # Push changes
        log "📤 Pushing changes to GitHub..."
        if git push origin main 2>/dev/null; then
            log "✅ Push successful"
        else
            warn "Push failed - may need to set up authentication"
            
            # Try to push anyway
            if git push -u origin main 2>/dev/null; then
                log "✅ Push successful with upstream"
            else
                error "Push failed. Check GitHub authentication."
            fi
        fi
    else
        warn "Commit failed"
    fi
fi

# Restore stashed changes if any
if git stash list | grep -q "Auto-stash before sync"; then
    log "🔄 Restoring stashed changes..."
    git stash pop 2>/dev/null || warn "Could not restore stashed changes"
fi

# Generate sync report
SYNC_TIME=$(date '+%Y-%m-%d %H:%M:%S')
BRANCH=$(git branch --show-current 2>/dev/null || echo "main")
LAST_COMMIT=$(git log -1 --format="%h - %s" 2>/dev/null || echo "No commits")

cat > logs/last-sync.json << EOF
{
    "sync_time": "$SYNC_TIME",
    "branch": "$BRANCH",
    "last_commit": "$LAST_COMMIT",
    "remote_changes": $REMOTE_CHANGES,
    "local_changes": $LOCAL_CHANGES,
    "status": "completed"
}
EOF

log "📊 Sync report saved to logs/last-sync.json"

# Check service health after sync
if ./scripts/health-check.sh > /dev/null 2>&1; then
    log "✅ Service health check passed"
else
    warn "Service may need attention after sync"
fi

echo ""
log "🎉 Git synchronization completed!"
log "📊 Branch: $BRANCH"
log "📝 Last commit: $LAST_COMMIT"
log "🕐 Sync time: $SYNC_TIME"
echo ""
