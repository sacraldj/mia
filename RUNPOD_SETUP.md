# 🚀 Mi AI Service - RunPod Setup Guide

**НАСТРОИЛ РАЗ - РАБОТАЕТ НАВСЕГДА!**

## ⚡ Quick Start (5 минут)

### 1️⃣ Clone Repository
```bash
# В RunPod SSH терминале:
cd /workspace
git clone https://github.com/sacraldj/mia.git
cd mia
```

### 2️⃣ Quick Setup
```bash
# Запустить автоматическую настройку:
chmod +x scripts/quick-setup.sh
./scripts/quick-setup.sh
```

### 3️⃣ Configure Supabase
```bash
# Скопировать и настроить файл окружения:
cp env.example .env
nano .env  # Добавить ваши Supabase credentials
```

### 4️⃣ Start Service
```bash
# Запустить сервис:
./scripts/start.sh
```

### 5️⃣ Test Generation
```bash
# Протестировать генерацию:
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"beautiful mosque","style":"architecture"}'
```

**🎉 Готово! Сервис работает на порту 8000**

---

## 📋 Detailed Setup Instructions

### Prerequisites
- RunPod instance с GPU
- Supabase проект с настроенными таблицами
- (Опционально) GitHub token для private repo

### Step-by-Step Setup

#### 1. Environment Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies  
sudo apt install -y git curl wget python3-pip

# Clone repository
cd /workspace
git clone https://github.com/sacraldj/mia.git
cd mia
```

#### 2. Python Environment
```bash
# Install Python packages
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
```

#### 3. Configuration
```bash
# Copy environment template
cp env.example .env

# Edit configuration (add your Supabase credentials)
nano .env
```

Required environment variables:
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
```

#### 4. Service Management
```bash
# Start service
./scripts/start.sh

# Check status
./scripts/health-check.sh

# View logs
tail -f logs/service.log

# Stop service
./scripts/stop.sh

# Restart service
./scripts/restart.sh
```

#### 5. Enable Auto-Sync (Optional)
```bash
# Manual sync with GitHub
./scripts/sync.sh

# Create backup
./scripts/backup.sh

# The service will automatically sync every 5 minutes
```

---

## 🎨 API Usage Examples

### Generate Image
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "beautiful Islamic architecture",
    "style": "architecture",
    "quality": "premium",
    "width": 1024,
    "height": 1024
  }'
```

### Check Task Status
```bash
curl "http://localhost:8000/task/TASK_ID"
```

### Get Service Stats
```bash
curl "http://localhost:8000/stats"
```

### Health Check
```bash
curl "http://localhost:8000/health"
```

---

## 🔄 Automatic Features

### Git Synchronization
- ✅ **Every 5 minutes**: Pull changes from GitHub
- ✅ **Auto-restart**: Service restarts if critical files change
- ✅ **Auto-commit**: Local changes committed and pushed

### Automatic Backup
- ✅ **Every hour**: Backup configurations and recent images
- ✅ **Cloud storage**: All backups stored in GitHub
- ✅ **Retention**: Keep last 10 configs, 50 images, 5 log files

### Service Monitoring
- ✅ **Health checks**: Automatic service health monitoring
- ✅ **Performance metrics**: Generation time, success rate
- ✅ **Auto-cleanup**: Old files cleaned up automatically

---

## 🎨 Arabic Styles Available

### 🕌 Architecture
Islamic architecture, geometric patterns, ornate details
```bash
{"style": "architecture"}
```

### ⭐ Golden Ornaments  
Luxury Arabic design with golden decorations
```bash
{"style": "golden"}
```

### 🎨 Geometric Patterns
Complex Islamic geometric patterns and arabesque
```bash
{"style": "patterns"}
```

### ✍️ Arabic Calligraphy
Beautiful Arabic calligraphy and Islamic art
```bash
{"style": "calligraphy"}
```

### 🌙 Ramadan Special
Ramadan decorations, crescent moon, lanterns
```bash
{"style": "ramadan"}
```

---

## 📊 Monitoring & Logs

### Available Endpoints
- `GET /` - Service information
- `GET /health` - Health check
- `GET /stats` - Service statistics
- `GET /metrics` - Prometheus metrics
- `POST /generate` - Generate image
- `GET /task/{id}` - Task status
- `GET /outputs/{filename}` - Download image

### Log Files
```bash
# Service logs
tail -f logs/service.log

# Sync logs
tail -f logs/sync.log

# Backup logs
tail -f logs/backup.log

# Error logs  
tail -f logs/error.log
```

### Service Status
```bash
# Check if service is running
ps aux | grep main.py

# Check port
netstat -tlnp | grep :8000

# Test connectivity
curl -f http://localhost:8000/health
```

---

## 🐳 Docker Alternative (Optional)

### Using Docker Compose
```bash
# Build and start with Docker
docker-compose up -d

# View logs
docker-compose logs -f

# Restart
docker-compose restart

# Stop
docker-compose down
```

### With Additional Services
```bash
# Start with Redis caching
docker-compose --profile redis up -d

# Start with full monitoring
docker-compose --profile redis --profile monitoring up -d
```

---

## 🔧 Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check Python dependencies
pip3 install -r requirements.txt

# Check port availability
netstat -tlnp | grep :8000

# Check logs for errors
tail -50 logs/service.log
```

#### Generation Fails
```bash
# Test basic generation
curl -X POST localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"test","style":"architecture"}'

# Check disk space
df -h

# Check permissions
ls -la /tmp/generated_images/
```

#### Supabase Connection Issues  
```bash
# Test connection
curl -H "apikey: YOUR_SERVICE_KEY" \
  "YOUR_SUPABASE_URL/rest/v1/generations?select=*&limit=1"

# Check environment variables
cat .env | grep SUPABASE
```

#### Git Sync Problems
```bash
# Check Git status
git status
git remote -v

# Manual sync
./scripts/sync.sh

# Reset if needed
git reset --hard origin/main
```

### Performance Optimization

#### GPU Memory
```bash
# Check GPU usage
nvidia-smi

# Reduce concurrent generations in config.json
"max_concurrent_generations": 1
```

#### Disk Space
```bash
# Check disk usage
df -h

# Clean old images
find /tmp/generated_images -name "*.png" -mtime +7 -delete

# Clean logs
truncate -s 0 logs/*.log
```

---

## 🚀 Advanced Configuration

### Custom Styles
Edit `config.json` to add new Arabic styles:
```json
{
  "arabic_styles": {
    "custom": {
      "name": "Custom Style",
      "icon": "🎭",
      "colors": ["#FF6B6B", "#4ECDC4"],
      "prompt_suffix": "custom Arabic art style",
      "quality_preset": "premium"
    }
  }
}
```

### Performance Tuning
```json
{
  "performance": {
    "max_concurrent_generations": 3,
    "queue_timeout_seconds": 300,
    "image_cache_size_mb": 1000,
    "cleanup_interval_hours": 2
  }
}
```

### Monitoring Setup
```json
{
  "monitoring": {
    "collect_metrics": true,
    "prometheus_port": 9090,
    "alert_thresholds": {
      "gpu_memory_percent": 90,
      "queue_size": 10,
      "error_rate_percent": 5
    }
  }
}
```

---

## 📞 Support

### Getting Help
1. Check logs: `tail -f logs/service.log`
2. Run diagnostics: `./scripts/health-check.sh`
3. Test basic functionality: `curl localhost:8000/health`
4. Check GitHub issues: https://github.com/sacraldj/mia/issues

### Reporting Issues
Include the following information:
- RunPod instance type and GPU
- Python version: `python3 --version`
- Service logs: `tail -100 logs/service.log`
- Error message and steps to reproduce

---

**🎉 Enjoy your automated Arabic AI image generation service!**

**НАСТРОИЛ РАЗ - РАБОТАЕТ НАВСЕГДА!** ⚡
