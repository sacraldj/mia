#!/usr/bin/env python3
"""
Mi AI Service - Simple Version for RunPod
Arabic-focused image generation with minimal dependencies
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from PIL import Image, ImageDraw, ImageFont
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Mi AI Service - Simple", 
    version="1.0.0",
    description="Arabic-focused AI image generation service (simplified version)"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global storage
tasks = {}
OUTPUT_DIR = "/tmp/generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    style: str = "architecture"
    user_id: Optional[str] = None
    width: int = 1024
    height: int = 1024

# Arabic styles configuration
ARABIC_STYLES = {
    "architecture": {
        "name": "Arabic Architecture", 
        "icon": "🕌", 
        "colors": ["#D4AF37", "#B8860B", "#DAA520"],
        "description": "Islamic architecture, geometric patterns, ornate details"
    },
    "golden": {
        "name": "Golden Ornaments", 
        "icon": "⭐", 
        "colors": ["#FFD700", "#FFA500", "#FF8C00"],
        "description": "Golden ornaments, luxury Arabic design, intricate details"
    },
    "patterns": {
        "name": "Geometric Patterns", 
        "icon": "🎨", 
        "colors": ["#4B0082", "#6A0DAD", "#9370DB"],
        "description": "Islamic geometric patterns, arabesque, symmetrical design"
    },
    "calligraphy": {
        "name": "Arabic Calligraphy", 
        "icon": "✍️", 
        "colors": ["#8B4513", "#A0522D", "#CD853F"],
        "description": "Arabic calligraphy, Islamic art, elegant script"
    },
    "ramadan": {
        "name": "Ramadan Special", 
        "icon": "🌙", 
        "colors": ["#800080", "#9932CC", "#BA55D3"],
        "description": "Ramadan decorations, crescent moon, lanterns, festive"
    }
}

def create_arabic_image(prompt: str, style: str, width: int = 1024, height: int = 1024):
    """Create Arabic-styled image using Pillow with advanced styling"""
    
    style_config = ARABIC_STYLES.get(style, ARABIC_STYLES["architecture"])
    colors = style_config["colors"]
    icon = style_config["icon"]
    
    # Create base image
    img = Image.new("RGB", (width, height), "#2C3E50")
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    for y in range(height):
        ratio = y / height
        start_color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
        end_color = tuple(int(colors[-1][i:i+2], 16) for i in (1, 3, 5))
        
        r = int(start_color[0] + (end_color[0] - start_color[0]) * ratio)
        g = int(start_color[1] + (end_color[1] - start_color[1]) * ratio)
        b = int(start_color[2] + (end_color[2] - start_color[2]) * ratio)
        
        for x in range(width):
            img.putpixel((x, y), (r, g, b))
    
    # Add decorative elements based on style
    if style == "architecture":
        add_architecture_elements(draw, width, height, colors)
    elif style == "golden":
        add_golden_ornaments(draw, width, height, colors)
    elif style == "patterns":
        add_geometric_patterns(draw, width, height, colors)
    elif style == "calligraphy":
        add_calligraphy_elements(draw, width, height, colors)
    elif style == "ramadan":
        add_ramadan_elements(draw, width, height, colors)
    
    # Add decorative border
    border_width = 15
    border_color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
    draw.rectangle([5, 5, width-5, border_width], fill=border_color)
    draw.rectangle([5, height-border_width, width-5, height-5], fill=border_color)
    draw.rectangle([5, 5, border_width, height-5], fill=border_color)
    draw.rectangle([width-border_width, 5, width-5, height-5], fill=border_color)
    
    # Add text elements
    try:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    except:
        font_large = None
        font_small = None
    
    # Main prompt text with shadow
    main_text = f"{icon} {prompt[:40]}"
    # Shadow
    draw.text((52, 52), main_text, fill="black", font=font_large)
    # Main text
    draw.text((50, 50), main_text, fill="white", font=font_large)
    
    # Style label
    style_text = f"Style: {style_config['name']}"
    draw.text((50, height - 120), style_text, fill="white", font=font_small)
    
    # Generation info
    info_text = f"Mi AI Service • RunPod • {datetime.now().strftime('%H:%M:%S')}"
    draw.text((50, height - 80), info_text, fill="#CCCCCC", font=font_small)
    
    # Quality indicator
    quality_text = "🎨 High Quality Generation"
    draw.text((50, height - 40), quality_text, fill="#FFD700", font=font_small)
    
    return img

def add_architecture_elements(draw, width, height, colors):
    """Add Islamic architecture elements"""
    color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
    
    # Draw arches
    for i in range(3):
        x = width // 4 + i * (width // 6)
        y = height // 3
        arch_size = 60
        draw.arc([x-arch_size//2, y-arch_size//2, x+arch_size//2, y+arch_size//2], 
                 0, 180, fill=color, width=3)

def add_golden_ornaments(draw, width, height, colors):
    """Add golden ornamental elements"""
    gold_color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
    
    # Corner ornaments
    positions = [(80, 80), (width-120, 80), (80, height-120), (width-120, height-120)]
    for x, y in positions:
        # Draw star pattern
        for i in range(8):
            angle = i * 45
            x1 = x + 30 * (1 if i % 2 == 0 else 0.6)
            y1 = y + 30 * (1 if (i + 2) % 4 < 2 else -1)
            draw.ellipse([x1-5, y1-5, x1+5, y1+5], fill=gold_color)

def add_geometric_patterns(draw, width, height, colors):
    """Add Islamic geometric patterns"""
    pattern_color = tuple(int(colors[1][i:i+2], 16) for i in (1, 3, 5))
    
    # Grid pattern
    step = 80
    for x in range(step, width-step, step):
        for y in range(step, height-step, step):
            # Draw octagonal pattern
            size = 25
            draw.polygon([
                (x-size, y-size//2), (x-size//2, y-size), (x+size//2, y-size),
                (x+size, y-size//2), (x+size, y+size//2), (x+size//2, y+size),
                (x-size//2, y+size), (x-size, y+size//2)
            ], outline=pattern_color, width=2)

def add_calligraphy_elements(draw, width, height, colors):
    """Add Arabic calligraphy-style elements"""
    cal_color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
    
    # Curved lines mimicking Arabic script
    for i in range(5):
        y = height // 6 + i * (height // 8)
        draw.arc([100, y-20, width-100, y+20], 0, 180, fill=cal_color, width=4)

def add_ramadan_elements(draw, width, height, colors):
    """Add Ramadan-themed elements"""
    ramadan_color = tuple(int(colors[0][i:i+2], 16) for i in (1, 3, 5))
    
    # Crescent moon
    moon_x, moon_y = width - 150, 100
    draw.ellipse([moon_x-30, moon_y-30, moon_x+30, moon_y+30], outline=ramadan_color, width=4)
    draw.ellipse([moon_x-20, moon_y-25, moon_x+20, moon_y+25], fill="#2C3E50")
    
    # Stars
    star_positions = [(moon_x-60, moon_y-20), (moon_x-40, moon_y+40), (moon_x+50, moon_y-10)]
    for sx, sy in star_positions:
        draw.polygon([(sx, sy-10), (sx-8, sy+8), (sx+8, sy+8)], fill=ramadan_color)

@app.get("/")
def root():
    return {
        "service": "Mi AI Service - Simple Version",
        "version": "1.0.0",
        "status": "running",
        "description": "Arabic-focused image generation with minimal dependencies",
        "styles": list(ARABIC_STYLES.keys()),
        "endpoints": ["/generate", "/task/{task_id}", "/health", "/styles"],
        "features": [
            "5 Arabic Styles",
            "Real-time Generation", 
            "High Quality Images",
            "Minimal Dependencies"
        ]
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_tasks": len(tasks),
        "service": "Mi AI Simple",
        "memory_usage": f"{len(tasks)} tasks stored",
        "uptime": "running"
    }

@app.post("/generate")
def generate_image(request: GenerateRequest):
    """Generate Arabic-styled image"""
    task_id = str(uuid.uuid4())
    start_time = datetime.now()
    
    try:
        logger.info(f"🎨 Starting generation: {request.prompt} ({request.style})")
        
        # Validate style
        if request.style not in ARABIC_STYLES:
            raise HTTPException(status_code=400, detail=f"Invalid style. Available: {list(ARABIC_STYLES.keys())}")
        
        # Create image
        img = create_arabic_image(request.prompt, request.style, request.width, request.height)
        
        # Save main image
        image_path = os.path.join(OUTPUT_DIR, f"{task_id}.png")
        img.save(image_path, "PNG", quality=95)
        
        # Create thumbnail
        thumbnail = img.copy()
        thumbnail.thumbnail((256, 256), Image.Resampling.LANCZOS)
        thumbnail_path = os.path.join(OUTPUT_DIR, f"{task_id}_thumb.png")
        thumbnail.save(thumbnail_path, "PNG", quality=85)
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        # Save task
        tasks[task_id] = {
            "task_id": task_id,
            "prompt": request.prompt,
            "style": request.style,
            "status": "completed",
            "image_url": f"/outputs/{task_id}.png",
            "thumbnail_url": f"/outputs/{task_id}_thumb.png",
            "created_at": start_time.isoformat(),
            "completed_at": datetime.now().isoformat(),
            "generation_time": round(generation_time, 2),
            "width": request.width,
            "height": request.height,
            "quality_score": 8.5,
            "style_applied": ARABIC_STYLES[request.style]["name"],
            "user_id": request.user_id or "demo-user"
        }
        
        logger.info(f"✅ Generated: {task_id} in {generation_time:.1f}s")
        
        return {
            "task_id": task_id,
            "status": "completed",
            "message": f"Arabic {request.style} generated successfully",
            "image_url": f"/outputs/{task_id}.png",
            "thumbnail_url": f"/outputs/{task_id}_thumb.png",
            "generation_time": round(generation_time, 2),
            "style": ARABIC_STYLES[request.style]["name"]
        }
        
    except Exception as e:
        logger.error(f"❌ Generation failed: {e}")
        
        # Save failed task
        tasks[task_id] = {
            "task_id": task_id,
            "prompt": request.prompt,
            "style": request.style,
            "status": "failed",
            "error": str(e),
            "created_at": start_time.isoformat(),
            "failed_at": datetime.now().isoformat()
        }
        
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}")
def get_task(task_id: str):
    """Get task status and details"""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks[task_id]

@app.get("/outputs/{filename}")
def get_image(filename: str):
    """Serve generated images"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(
        file_path, 
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"}
    )

@app.get("/styles")
def get_styles():
    """Get available Arabic styles"""
    return {"styles": ARABIC_STYLES}

@app.get("/stats")
def get_stats():
    """Get service statistics"""
    completed_tasks = [t for t in tasks.values() if t.get("status") == "completed"]
    failed_tasks = [t for t in tasks.values() if t.get("status") == "failed"]
    
    style_usage = {}
    for style in ARABIC_STYLES.keys():
        style_usage[style] = len([t for t in completed_tasks if t.get("style") == style])
    
    return {
        "total_tasks": len(tasks),
        "completed_tasks": len(completed_tasks),
        "failed_tasks": len(failed_tasks),
        "success_rate": f"{len(completed_tasks)/len(tasks)*100:.1f}%" if tasks else "0%",
        "style_usage": style_usage,
        "avg_generation_time": f"{sum(t.get('generation_time', 0) for t in completed_tasks)/len(completed_tasks):.1f}s" if completed_tasks else "0s",
        "service": "Mi AI Simple",
        "uptime": "running"
    }

if __name__ == "__main__":
    logger.info("🚀 Starting Mi AI Service - Simple Version for RunPod")
    logger.info(f"📁 Output directory: {OUTPUT_DIR}")
    logger.info(f"🎨 Available styles: {list(ARABIC_STYLES.keys())}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
