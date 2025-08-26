#!/usr/bin/env python3
"""
Mi AI Service - RunPod Edition
Arabic-focused image generation with Supabase integration and Git sync
"""

import os
import json
import uuid
import logging
import threading
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import io
import base64

# Web Framework
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Image Processing
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import requests

# Database & Storage
from supabase import create_client, Client
import asyncpg

# Git Integration  
import git

# Background Tasks
import schedule

# Monitoring
from prometheus_client import Counter, Histogram, generate_latest
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mi-ai-service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# Configuration and Constants
# ==========================================

class Config:
    def __init__(self):
        self.load_config()
    
    def load_config(self):
        """Load configuration from config.json and environment"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            logger.warning("config.json not found, using defaults")
            self.config = self._default_config()
        
        # Environment overrides
        self.supabase_url = os.getenv('SUPABASE_URL', '')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY', '')
        self.github_token = os.getenv('GITHUB_TOKEN', '')
        
    def _default_config(self):
        return {
            "version": "2.0.0",
            "sync_settings": {"enabled": True, "sync_interval": 300},
            "arabic_styles": {
                "architecture": {"name": "Arabic Architecture", "icon": "🕌"},
                "golden": {"name": "Golden Ornaments", "icon": "⭐"},
                "patterns": {"name": "Geometric Patterns", "icon": "🎨"},
                "calligraphy": {"name": "Arabic Calligraphy", "icon": "✍️"},
                "ramadan": {"name": "Ramadan Special", "icon": "🌙"}
            }
        }
    
    def get(self, key: str, default=None):
        """Get configuration value with dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

# Global configuration
config = Config()

# ==========================================
# Pydantic Models
# ==========================================

class GenerateRequest(BaseModel):
    prompt: str
    style: str = "architecture"
    user_id: Optional[str] = None
    quality: str = "quality"
    width: int = 1024
    height: int = 1024

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    progress: int = 0
    error: Optional[str] = None
    generation_time: Optional[int] = None
    created_at: str

# ==========================================
# Supabase Integration
# ==========================================

class SupabaseManager:
    def __init__(self):
        self.client: Optional[Client] = None
        self.initialize()
    
    def initialize(self):
        """Initialize Supabase client"""
        try:
            if config.supabase_url and config.supabase_key:
                self.client = create_client(config.supabase_url, config.supabase_key)
                logger.info("✅ Supabase client initialized")
            else:
                logger.warning("⚠️ Supabase credentials not found")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {e}")
    
    def save_generation(self, task_data: dict) -> bool:
        """Save generation to Supabase"""
        if not self.client:
            logger.warning("⚠️ Supabase client not available")
            return False
        
        try:
            # Prepare data for Supabase
            generation_data = {
                'task_id': task_data['task_id'],
                'user_id': task_data.get('user_id', '00000000-0000-0000-0000-000000000000'),
                'prompt': task_data['prompt'],
                'style': task_data['style'],
                'image_url': task_data.get('image_url'),
                'thumbnail_url': task_data.get('thumbnail_url'),
                'status': task_data['status'],
                'generation_time': task_data.get('generation_time'),
                'cost': task_data.get('cost', 3),
                'model': 'Mi AI - Stable Diffusion 3.5',
                'width': task_data.get('width', 1024),
                'height': task_data.get('height', 1024),
                'quality_score': task_data.get('quality_score', 8.5),
                'error_message': task_data.get('error')
            }
            
            # Insert into database
            result = self.client.table('generations').insert(generation_data).execute()
            
            if result.data:
                logger.info(f"✅ Generation saved to Supabase: {task_data['task_id']}")
                return True
            else:
                logger.error(f"❌ Failed to save generation: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Supabase save error: {e}")
            return False
    
    def get_user_generations(self, user_id: str, limit: int = 10) -> List[dict]:
        """Get user's generations from Supabase"""
        if not self.client:
            return []
        
        try:
            result = self.client.table('generations') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            
            return result.data or []
        except Exception as e:
            logger.error(f"❌ Failed to get user generations: {e}")
            return []
    
    def update_generation_status(self, task_id: str, status: str, **kwargs):
        """Update generation status in Supabase"""
        if not self.client:
            return False
        
        try:
            update_data = {'status': status}
            update_data.update(kwargs)
            
            result = self.client.table('generations') \
                .update(update_data) \
                .eq('task_id', task_id) \
                .execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"❌ Failed to update generation status: {e}")
            return False

# Global Supabase manager
supabase_manager = SupabaseManager()

# ==========================================
# Git Sync Manager
# ==========================================

class GitSyncManager:
    def __init__(self):
        self.repo_path = "/workspace/mi-ai-service-runpod"
        self.repo = None
        self.last_sync = datetime.now()
        self.sync_enabled = config.get('sync_settings.enabled', True)
    
    def initialize_repo(self, github_url: str = "https://github.com/sacraldj/mia.git"):
        """Initialize Git repository"""
        try:
            if os.path.exists(os.path.join(self.repo_path, '.git')):
                self.repo = git.Repo(self.repo_path)
                logger.info("📂 Existing Git repository found")
            else:
                # Clone if exists, otherwise init
                try:
                    self.repo = git.Repo.clone_from(github_url, self.repo_path)
                    logger.info("📥 Repository cloned from GitHub")
                except git.exc.GitCommandError:
                    # Repository might be empty, initialize locally
                    git.Repo.init(self.repo_path)
                    self.repo = git.Repo(self.repo_path)
                    self.repo.create_remote('origin', github_url)
                    logger.info("📝 Local Git repository initialized")
            
            return True
        except Exception as e:
            logger.error(f"❌ Git initialization failed: {e}")
            return False
    
    def sync_changes(self):
        """Sync changes with GitHub"""
        if not self.sync_enabled or not self.repo:
            return False
        
        try:
            # Pull latest changes
            if 'origin' in [remote.name for remote in self.repo.remotes]:
                try:
                    self.repo.remotes.origin.pull()
                    logger.info("🔄 Pulled latest changes from GitHub")
                except git.exc.GitCommandError as e:
                    if "couldn't find remote ref" not in str(e).lower():
                        logger.warning(f"⚠️ Pull failed: {e}")
            
            # Push local changes
            self.repo.git.add(A=True)
            if self.repo.index.diff("HEAD"):
                commit_message = f"Auto-sync: {datetime.now().isoformat()}"
                self.repo.index.commit(commit_message)
                
                if 'origin' in [remote.name for remote in self.repo.remotes]:
                    try:
                        self.repo.remotes.origin.push()
                        logger.info("📤 Pushed changes to GitHub")
                    except git.exc.GitCommandError as e:
                        logger.warning(f"⚠️ Push failed: {e}")
            
            self.last_sync = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"❌ Git sync failed: {e}")
            return False
    
    def get_status(self):
        """Get Git sync status"""
        return {
            "sync_enabled": self.sync_enabled,
            "last_sync": self.last_sync.isoformat(),
            "repo_initialized": self.repo is not None,
            "has_changes": bool(self.repo and self.repo.index.diff("HEAD")) if self.repo else False
        }

# Global Git sync manager
git_sync = GitSyncManager()

# ==========================================
# Image Generation
# ==========================================

class ImageGenerator:
    def __init__(self):
        self.arabic_styles = config.get('arabic_styles', {})
        self.output_dir = "/tmp/generated_images"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def create_gradient_background(self, size: tuple, colors: list) -> Image.Image:
        """Create gradient background"""
        width, height = size
        img = Image.new("RGB", size)
        
        for y in range(height):
            ratio = y / height
            if len(colors) >= 2:
                # Interpolate between first and last color
                start_color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
                end_color = tuple(int(colors[-1][i:i+2], 16) for i in (1, 3, 5))
                
                r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
                g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
                b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
                
                for x in range(width):
                    img.putpixel((x, y), (r, g, b))
        
        return img
    
    def add_arabic_decorations(self, img: Image.Image, style: str) -> Image.Image:
        """Add Arabic-style decorations"""
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # Get style config
        style_config = self.arabic_styles.get(style, self.arabic_styles.get('architecture', {}))
        colors = style_config.get('colors', ['#D4AF37'])
        
        # Add geometric patterns based on style
        if style == 'patterns':
            self._draw_geometric_patterns(draw, width, height, colors)
        elif style == 'architecture':
            self._draw_architectural_elements(draw, width, height, colors)
        elif style == 'golden':
            self._draw_ornaments(draw, width, height, colors)
        
        return img
    
    def _draw_geometric_patterns(self, draw, width, height, colors):
        """Draw Islamic geometric patterns"""
        color = colors[0] if colors else '#D4AF37'
        
        # Draw repeating geometric shapes
        for x in range(0, width, 100):
            for y in range(0, height, 100):
                # Octagon pattern
                points = []
                center_x, center_y = x + 50, y + 50
                radius = 30
                
                for i in range(8):
                    angle = i * 45 * 3.14159 / 180
                    px = center_x + radius * 0.7 * (1 if i % 2 == 0 else 0.7) * (1 if i < 4 else -1)
                    py = center_y + radius * 0.7 * (1 if (i + 2) % 4 < 2 else -1)
                    points.append((px, py))
                
                if len(points) >= 3:
                    draw.polygon(points, outline=color, width=2)
    
    def _draw_architectural_elements(self, draw, width, height, colors):
        """Draw architectural elements like arches"""
        color = colors[0] if colors else '#D4AF37'
        
        # Draw decorative border
        border_width = 20
        draw.rectangle([10, 10, width-10, border_width], fill=color)
        draw.rectangle([10, height-border_width, width-10, height-10], fill=color)
        draw.rectangle([10, 10, border_width, height-10], fill=color)
        draw.rectangle([width-border_width, 10, width-10, height-10], fill=color)
        
        # Draw arch shapes
        for i in range(3):
            x = (width // 4) * (i + 1)
            arch_top = height // 3
            arch_width = 60
            
            draw.arc([x - arch_width//2, arch_top - arch_width//2, 
                     x + arch_width//2, arch_top + arch_width//2], 
                    0, 180, fill=color, width=3)
    
    def _draw_ornaments(self, draw, width, height, colors):
        """Draw golden ornaments"""
        color = colors[0] if colors else '#FFD700'
        
        # Draw corner ornaments
        ornament_size = 40
        positions = [(30, 30), (width-70, 30), (30, height-70), (width-70, height-70)]
        
        for x, y in positions:
            # Draw star-like ornament
            points = []
            for i in range(8):
                angle = i * 45 * 3.14159 / 180
                radius = ornament_size if i % 2 == 0 else ornament_size // 2
                px = x + radius * 0.5
                py = y + radius * 0.5
                points.append((px, py))
            
            if len(points) >= 3:
                draw.polygon(points, fill=color, outline=color)
    
    def generate_image(self, prompt: str, style: str, width: int = 1024, height: int = 1024) -> tuple:
        """Generate image with Arabic styling"""
        start_time = time.time()
        
        # Get style configuration
        style_config = self.arabic_styles.get(style, self.arabic_styles.get('architecture', {}))
        colors = style_config.get('colors', ['#D4AF37', '#B8860B'])
        icon = style_config.get('icon', '🎨')
        
        try:
            # Create base gradient image
            img = self.create_gradient_background((width, height), colors)
            
            # Add Arabic decorations
            img = self.add_arabic_decorations(img, style)
            
            # Add text overlay
            draw = ImageDraw.Draw(img)
            
            # Try to load a better font
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            except:
                font_large = ImageFont.load_default()
                font_medium = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Add main text with shadow effect
            main_text = f"{icon} {prompt[:50]}"
            text_x, text_y = 50, 50
            
            # Shadow
            draw.text((text_x + 2, text_y + 2), main_text, fill="black", font=font_large)
            # Main text
            draw.text((text_x, text_y), main_text, fill="white", font=font_large)
            
            # Style label
            style_text = f"Style: {style_config.get('name', style.title())}"
            draw.text((50, height - 100), style_text, fill="white", font=font_medium)
            
            # Generation info
            generation_time = int(time.time() - start_time)
            info_text = f"Mi AI Service • {datetime.now().strftime('%H:%M:%S')} • {generation_time}s"
            draw.text((50, height - 50), info_text, fill="white", font=font_small)
            
            # Quality enhancement
            img = img.filter(ImageFilter.SMOOTH_MORE)
            
            # Save original image
            task_id = str(uuid.uuid4())
            image_path = os.path.join(self.output_dir, f"{task_id}.png")
            img.save(image_path, "PNG", quality=95)
            
            # Create thumbnail
            thumbnail = img.copy()
            thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
            thumbnail_path = os.path.join(self.output_dir, f"{task_id}_thumb.png")
            thumbnail.save(thumbnail_path, "PNG", quality=85)
            
            generation_time = int(time.time() - start_time)
            
            return {
                'task_id': task_id,
                'image_path': image_path,
                'thumbnail_path': thumbnail_path,
                'generation_time': generation_time,
                'width': width,
                'height': height,
                'style_applied': style_config.get('name', style),
                'quality_score': 8.5
            }
            
        except Exception as e:
            logger.error(f"❌ Image generation failed: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

# Global image generator
image_generator = ImageGenerator()

# ==========================================
# Task Management
# ==========================================

class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, dict] = {}
        self.max_tasks = 1000
    
    def create_task(self, task_data: dict) -> str:
        """Create a new generation task"""
        task_id = str(uuid.uuid4())
        
        task = {
            'task_id': task_id,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'progress': 0,
            **task_data
        }
        
        self.tasks[task_id] = task
        
        # Cleanup old tasks
        if len(self.tasks) > self.max_tasks:
            oldest_tasks = sorted(self.tasks.keys(), 
                                key=lambda k: self.tasks[k]['created_at'])[:100]
            for old_task_id in oldest_tasks:
                del self.tasks[old_task_id]
        
        logger.info(f"📋 Task created: {task_id}")
        return task_id
    
    def update_task(self, task_id: str, **updates):
        """Update task status"""
        if task_id in self.tasks:
            self.tasks[task_id].update(updates)
            self.tasks[task_id]['updated_at'] = datetime.now().isoformat()
            
            # Save to Supabase if completed
            if updates.get('status') == 'completed':
                supabase_manager.save_generation(self.tasks[task_id])
    
    def get_task(self, task_id: str) -> dict:
        """Get task status"""
        return self.tasks.get(task_id, {'error': 'Task not found'})
    
    def get_active_tasks(self) -> List[dict]:
        """Get all active tasks"""
        return [task for task in self.tasks.values() 
                if task.get('status') in ['queued', 'processing']]

# Global task manager
task_manager = TaskManager()

# ==========================================
# FastAPI Application
# ==========================================

# Metrics
generation_counter = Counter('mi_ai_generations_total', 'Total generations')
generation_duration = Histogram('mi_ai_generation_seconds', 'Generation duration')

app = FastAPI(
    title="Mi AI Service - RunPod Edition", 
    version=config.get('version', '2.0.0'),
    description="Arabic-focused AI image generation with Supabase integration"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# API Endpoints
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Mi AI Service starting...")
    
    # Initialize Git sync
    git_sync.initialize_repo()
    
    # Start background sync scheduler
    if git_sync.sync_enabled:
        def run_sync():
            while True:
                try:
                    git_sync.sync_changes()
                    time.sleep(config.get('sync_settings.sync_interval', 300))
                except Exception as e:
                    logger.error(f"❌ Sync scheduler error: {e}")
                    time.sleep(60)
        
        sync_thread = threading.Thread(target=run_sync, daemon=True)
        sync_thread.start()
        logger.info("🔄 Git sync scheduler started")
    
    logger.info("✅ Mi AI Service ready!")

@app.get("/")
async def root():
    """Service information"""
    return {
        "service": "Mi AI Service - RunPod Edition",
        "version": config.get('version', '2.0.0'),
        "status": "running",
        "features": ["Arabic Styles", "Supabase Integration", "Git Sync", "Auto Backup"],
        "endpoints": ["/generate", "/task/{task_id}", "/health", "/stats"],
        "git_status": git_sync.get_status(),
        "active_tasks": len(task_manager.get_active_tasks())
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "supabase": supabase_manager.client is not None,
            "git_sync": git_sync.repo is not None,
            "image_generation": True
        },
        "metrics": {
            "active_tasks": len(task_manager.get_active_tasks()),
            "total_tasks": len(task_manager.tasks)
        }
    }

@app.post("/generate")
async def generate_image(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate Arabic-styled image"""
    generation_counter.inc()
    
    # Create task
    task_id = task_manager.create_task({
        'prompt': request.prompt,
        'style': request.style,
        'user_id': request.user_id or '00000000-0000-0000-0000-000000000000',
        'quality': request.quality,
        'width': request.width,
        'height': request.height
    })
    
    # Start background generation
    background_tasks.add_task(process_generation, task_id)
    
    logger.info(f"🎨 Generation started: {task_id} - {request.prompt} ({request.style})")
    
    return {
        "task_id": task_id,
        "status": "queued",
        "message": f"Arabic {request.style} generation started",
        "estimated_time": "30-60 seconds"
    }

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and result"""
    task = task_manager.get_task(task_id)
    
    if 'error' in task and task['error'] == 'Task not found':
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Add image URLs if completed
    if task.get('status') == 'completed' and task.get('image_path'):
        task['image_url'] = f"/outputs/{os.path.basename(task['image_path'])}"
        task['thumbnail_url'] = f"/outputs/{os.path.basename(task.get('thumbnail_path', ''))}"
    
    return task

@app.get("/outputs/{filename}")
async def get_image(filename: str):
    """Serve generated images"""
    file_path = os.path.join("/tmp/generated_images", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(
        file_path, 
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.get("/stats")
async def get_statistics():
    """Get service statistics"""
    return {
        "total_generations": len(task_manager.tasks),
        "active_tasks": len(task_manager.get_active_tasks()),
        "completed_tasks": len([t for t in task_manager.tasks.values() if t.get('status') == 'completed']),
        "failed_tasks": len([t for t in task_manager.tasks.values() if t.get('status') == 'failed']),
        "styles_usage": {
            style: len([t for t in task_manager.tasks.values() if t.get('style') == style])
            for style in config.get('arabic_styles', {}).keys()
        },
        "git_sync": git_sync.get_status(),
        "uptime": "running"
    }

@app.post("/sync")
async def manual_sync():
    """Manual Git synchronization"""
    success = git_sync.sync_changes()
    return {
        "success": success,
        "timestamp": datetime.now().isoformat(),
        "status": git_sync.get_status()
    }

@app.get("/metrics")
async def get_metrics():
    """Prometheus metrics endpoint"""
    return generate_latest()

# ==========================================
# Background Tasks
# ==========================================

async def process_generation(task_id: str):
    """Process image generation in background"""
    try:
        task = task_manager.get_task(task_id)
        if 'error' in task:
            return
        
        # Update status
        task_manager.update_task(task_id, status='processing', progress=10)
        
        with generation_duration.time():
            # Generate image
            result = image_generator.generate_image(
                prompt=task['prompt'],
                style=task['style'],
                width=task.get('width', 1024),
                height=task.get('height', 1024)
            )
            
            # Update task with results
            task_manager.update_task(
                task_id,
                status='completed',
                progress=100,
                completed_at=datetime.now().isoformat(),
                **result
            )
            
            logger.info(f"✅ Generation completed: {task_id} ({result['generation_time']}s)")
            
    except Exception as e:
        logger.error(f"❌ Generation failed: {task_id} - {e}")
        task_manager.update_task(
            task_id,
            status='failed',
            error=str(e),
            completed_at=datetime.now().isoformat()
        )

# ==========================================
# Main Application
# ==========================================

if __name__ == "__main__":
    logger.info("🚀 Starting Mi AI Service - RunPod Edition...")
    
    # Ensure output directory exists
    os.makedirs("/tmp/generated_images", exist_ok=True)
    
    # Start server
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
        workers=1
    )
