#!/bin/bash
# Mi AI Service - Quick Setup Script for RunPod
# ============================================

echo "🚀 Mi AI Service - Quick Setup"
echo "==============================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "main.py" ] || [ ! -f "config.json" ]; then
    error "Run this script from the mi-ai-service-runpod directory"
    exit 1
fi

log "📍 Current directory: $(pwd)"
log "🐍 Python version: $(python3 --version)"

# Create necessary directories
log "📁 Creating directories..."
mkdir -p logs backups outputs temp

# Update system packages
log "📦 Updating system packages..."
apt-get update -y > /dev/null 2>&1 || warn "Could not update packages (not critical)"

# Install system dependencies
log "⚙️ Installing system dependencies..."
apt-get install -y git curl wget fonts-dejavu-core > /dev/null 2>&1 || warn "Some system packages failed to install"

# Upgrade pip
log "📊 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python dependencies
log "🐍 Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        log "✅ All Python dependencies installed successfully"
    else
        error "Failed to install some Python dependencies"
        echo "Trying individual installation..."
        
        # Install critical packages individually
        python3 -m pip install fastapi uvicorn pillow requests supabase gitpython schedule
        warn "Some optional dependencies may have failed - service will still work"
    fi
else
    error "requirements.txt not found"
    exit 1
fi

# Set up environment variables
log "🔐 Setting up environment..."
if [ ! -f ".env" ]; then
    log "Creating .env template..."
    cat > .env << 'EOF'
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_supabase_service_role_key

# GitHub Configuration (Optional)
GITHUB_TOKEN=your_github_personal_access_token

# Service Configuration
SERVICE_NAME=Mi AI Service
SERVICE_VERSION=2.0.0
PORT=8000

# Image Generation Settings
MAX_IMAGE_SIZE=1024
GENERATION_TIMEOUT=300
EOF
    warn "Created .env template - please configure your Supabase credentials"
else
    log "✅ .env file already exists"
fi

# Make scripts executable
log "🔧 Making scripts executable..."
chmod +x scripts/*.sh

# Create service status check
log "🏥 Setting up health check..."
cat > scripts/health-check.sh << 'EOF'
#!/bin/bash
curl -s http://localhost:8000/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Service is healthy"
    exit 0
else
    echo "❌ Service is not responding"
    exit 1
fi
EOF
chmod +x scripts/health-check.sh

# Create quick start script
log "⚡ Creating quick start script..."
cat > scripts/start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Mi AI Service..."

# Kill any existing processes
pkill -f "python.*main.py" 2>/dev/null

# Start the service
nohup python3 main.py > logs/service.log 2>&1 &

echo "📊 Service starting in background..."
echo "📋 Logs: tail -f logs/service.log"
echo "🏥 Health check: curl http://localhost:8000/health"

# Wait a moment and check if it started
sleep 3
if pgrep -f "python.*main.py" > /dev/null; then
    echo "✅ Service started successfully!"
    echo "🌐 Service available at: http://localhost:8000"
else
    echo "❌ Service failed to start. Check logs/service.log"
fi
EOF
chmod +x scripts/start.sh

# Create stop script  
log "🛑 Creating stop script..."
cat > scripts/stop.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Mi AI Service..."

# Kill Python processes
if pkill -f "python.*main.py"; then
    echo "✅ Service stopped"
else
    echo "⚠️ No running service found"
fi
EOF
chmod +x scripts/stop.sh

# Create restart script
log "🔄 Creating restart script..."
cat > scripts/restart.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Mi AI Service..."

./scripts/stop.sh
sleep 2
./scripts/start.sh
EOF
chmod +x scripts/restart.sh

# Git configuration
log "📝 Setting up Git..."
if [ ! -d ".git" ]; then
    git init
    git remote add origin https://github.com/sacraldj/mia.git
    log "✅ Git repository initialized"
else
    log "✅ Git repository already exists"
fi

# Configure Git user (generic for RunPod)
git config user.name "RunPod Service" 2>/dev/null
git config user.email "service@runpod.local" 2>/dev/null

# Create .gitignore
log "📄 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# Environment variables
.env
.env.local
.env.production

# Logs
logs/*.log
*.log

# Temporary files
temp/
tmp/
outputs/
*.tmp

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Service specific
generated_images/
backups/local/
EOF

# Initial commit
log "📤 Creating initial commit..."
git add .
git commit -m "Initial Mi AI Service setup" 2>/dev/null || log "📝 No changes to commit"

# Final status
echo ""
log "🎉 QUICK SETUP COMPLETED!"
echo "=========================="
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Configure your .env file with Supabase credentials"
echo "2. Start the service: ./scripts/start.sh"
echo "3. Check health: curl http://localhost:8000/health"
echo "4. Test generation: curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{\"prompt\":\"mosque\",\"style\":\"architecture\"}'"
echo ""
echo -e "${BLUE}📚 Available Scripts:${NC}"
echo "• ./scripts/start.sh     - Start the service"
echo "• ./scripts/stop.sh      - Stop the service"  
echo "• ./scripts/restart.sh   - Restart the service"
echo "• ./scripts/health-check.sh - Check service health"
echo ""
echo -e "${BLUE}📊 Monitoring:${NC}"
echo "• Service logs: tail -f logs/service.log"
echo "• Health check: http://localhost:8000/health"
echo "• Statistics: http://localhost:8000/stats"
echo "• API docs: http://localhost:8000/docs"
echo ""
echo -e "${GREEN}🚀 ГОТОВ К РАБОТЕ! (READY TO GO!)${NC}"
