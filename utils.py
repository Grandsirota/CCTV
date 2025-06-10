# utils.py - CPU Optimized utility functions

import os
import requests
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor
import gc

# Telegram Configuration
TELEGRAM_BOT_TOKEN = '7687849270:AAG5YgRP64KM13hbjZKFTPgA29DUXbm3ens'
TELEGRAM_CHAT_ID = '-4809459710'

# Enhanced rate limiting
last_notification_time = {}
NOTIFICATION_COOLDOWN = 60  # Increased to 1 minute
MAX_NOTIFICATIONS_PER_HOUR = 20

# Thread pool for async operations
notification_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="notification")

def ensure_dirs(directory_list):
    """Ensure directories exist"""
    for directory in directory_list:
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(f"Error creating directory {directory}: {e}")

def send_telegram_alert(message):
    """Send alert with enhanced rate limiting and async processing"""
    try:
        current_time = time.time()
        camera_key = "general"
        
        # Enhanced rate limiting
        if camera_key in last_notification_time:
            time_diff = current_time - last_notification_time[camera_key]
            if time_diff < NOTIFICATION_COOLDOWN:
                print(f"⏰ Alert rate limited ({time_diff:.1f}s < {NOTIFICATION_COOLDOWN}s)")
                return False
        
        # Check hourly limit
        hour_start = current_time - 3600
        recent_notifications = sum(1 for t in last_notification_time.values() if t > hour_start)
        if recent_notifications >= MAX_NOTIFICATIONS_PER_HOUR:
            print(f"📨 Hourly notification limit reached ({recent_notifications}/{MAX_NOTIFICATIONS_PER_HOUR})")
            return False
        
        # Send in background thread
        def send_async():
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                params = {
                    "chat_id": TELEGRAM_CHAT_ID,
                    "text": message,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True
                }
                
                response = requests.get(url, params=params, timeout=5)  # Reduced timeout
                
                if response.status_code == 200:
                    last_notification_time[camera_key] = current_time
                    print("📱 Telegram alert sent successfully")
                    return True
                else:
                    print(f"❌ Telegram Error ({response.status_code}): {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Telegram alert failed: {e}")
                return False
        
        # Submit to thread pool
        notification_executor.submit(send_async)
        return True
        
    except Exception as e:
        print(f"❌ Alert setup failed: {e}")
        return False

def send_telegram_photo(image_path, caption):
    """Send photo with optimized file handling"""
    try:
        # Validate file
        if not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
            print(f"❌ Invalid image file: {image_path}")
            return False
        
        # Rate limiting for photos
        current_time = time.time()
        photo_key = "photo"
        
        if photo_key in last_notification_time:
            time_diff = current_time - last_notification_time[photo_key]
            if time_diff < NOTIFICATION_COOLDOWN:
                print(f"⏰ Photo rate limited ({time_diff:.1f}s)")
                return False
        
        # Send in background thread
        def send_photo_async():
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                
                # Optimize file reading
                with open(image_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {
                        'chat_id': TELEGRAM_CHAT_ID,
                        'caption': caption[:1000],  # Limit caption length
                        'parse_mode': 'HTML'
                    }
                    
                    response = requests.post(url, files=files, data=data, timeout=15)
                
                if response.status_code == 200:
                    last_notification_time[photo_key] = current_time
                    print("📷 Telegram photo sent successfully")
                    return True
                else:
                    print(f"❌ Photo Error ({response.status_code}): {response.text}")
                    return False
                    
            except Exception as e:
                print(f"❌ Photo send failed: {e}")
                return False
            finally:
                # Cleanup
                gc.collect()
        
        # Submit to thread pool
        notification_executor.submit(send_photo_async)
        return True
        
    except Exception as e:
        print(f"❌ Photo setup failed: {e}")
        return False

def get_datetime_str(format="%Y-%m-%d %H:%M:%S"):
    """Get current datetime string"""
    return datetime.now().strftime(format)

def get_date_str(format="%Y-%m-%d"):
    """Get current date string"""
    return datetime.now().strftime(format)

def format_time_diff(seconds):
    """Format time difference to human readable string"""
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.0f} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"

def is_gpu_available():
    """Check GPU availability with caching"""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def get_optimized_device():
    """Get the best available device for inference"""
    try:
        import torch
        if torch.cuda.is_available():
            # Check if CUDA is actually faster for small models
            device_name = torch.cuda.get_device_name(0)
            memory = torch.cuda.get_device_properties(0).total_memory
            
            # For small models like YOLOv8n, CPU might be faster due to overhead
            if memory < 4 * 1024**3:  # Less than 4GB VRAM
                print("⚡ Using CPU (GPU overhead not worth it for small models)")
                return 'cpu'
            else:
                print(f"🚀 Using GPU: {device_name}")
                return 'cuda:0'
        else:
            print("💻 Using CPU (no GPU available)")
            return 'cpu'
    except Exception as e:
        print(f"❌ Device detection error: {e}")
        return 'cpu'

def get_system_info():
    """Get optimized system information"""
    try:
        import psutil
        
        # Get basic info with minimal overhead
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu": {
                "usage": round(cpu_percent, 1),
                "cores": psutil.cpu_count()
            },
            "memory": {
                "usage_percent": round(memory.percent, 1),
                "used_gb": round(memory.used / (1024**3), 1),
                "total_gb": round(memory.total / (1024**3), 1)
            },
            "disk": {
                "usage_percent": round(disk.percent, 1),
                "free_gb": round(disk.free / (1024**3), 1)
            }
        }
    except Exception as e:
        print(f"❌ System info error: {e}")
        return {
            "cpu": {"usage": 0, "cores": 0},
            "memory": {"usage_percent": 0, "used_gb": 0, "total_gb": 0},
            "disk": {"usage_percent": 0, "free_gb": 0}
        }

def test_telegram_connection():
    """Test Telegram connection with timeout"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            bot_info = response.json()
            if bot_info.get('ok'):
                bot_name = bot_info['result'].get('username', 'Unknown')
                return True, f"✅ Connected to bot: @{bot_name}"
            else:
                return False, "❌ Bot authentication failed"
        else:
            return False, f"❌ HTTP Error: {response.status_code}"
            
    except Exception as e:
        return False, f"❌ Connection error: {str(e)}"

def clean_old_images(images_dir, days_to_keep=3):
    """Optimized cleanup of old images"""
    try:
        import time
        from pathlib import Path
        
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        deleted_count = 0
        deleted_size = 0
        
        def cleanup_worker():
            nonlocal deleted_count, deleted_size
            
            for root, dirs, files in os.walk(images_dir):
                for file in files:
                    if file.endswith('.jpg'):
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.getmtime(file_path) < cutoff_time:
                                file_size = os.path.getsize(file_path)
                                os.remove(file_path)
                                deleted_count += 1
                                deleted_size += file_size
                        except Exception as e:
                            print(f"❌ Error deleting {file_path}: {e}")
            
            # Remove empty directories
            for root, dirs, files in os.walk(images_dir, topdown=False):
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    try:
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                    except Exception:
                        pass
        
        # Run cleanup in background
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        cleanup_thread.join(timeout=30)  # Max 30 seconds
        
        deleted_mb = deleted_size / (1024 * 1024)
        print(f"🧹 Cleaned {deleted_count} images ({deleted_mb:.1f} MB)")
        return deleted_count
        
    except Exception as e:
        print(f"❌ Cleanup error: {e}")
        return 0

def optimize_image_quality(image_path, max_size_kb=500):
    """Optimize image file size for faster uploads"""
    try:
        import cv2
        
        if not os.path.exists(image_path):
            return False
        
        # Check current size
        current_size = os.path.getsize(image_path) / 1024  # KB
        
        if current_size <= max_size_kb:
            return True  # Already optimized
        
        # Load and compress image
        img = cv2.imread(image_path)
        if img is None:
            return False
        
        # Calculate compression quality
        quality = max(30, int(85 * (max_size_kb / current_size)))
        
        # Save with compression
        cv2.imwrite(image_path, img, [cv2.IMWRITE_JPEG_QUALITY, quality])
        
        new_size = os.path.getsize(image_path) / 1024
        print(f"📸 Optimized image: {current_size:.1f}KB → {new_size:.1f}KB")
        
        return True
        
    except Exception as e:
        print(f"❌ Image optimization error: {e}")
        return False

def monitor_resource_usage():
    """Monitor and log resource usage"""
    def monitor_worker():
        while True:
            try:
                info = get_system_info()
                cpu_usage = info['cpu']['usage']
                memory_usage = info['memory']['usage_percent']
                
                # Log high usage
                if cpu_usage > 90:
                    print(f"⚠️ High CPU usage: {cpu_usage}%")
                if memory_usage > 85:
                    print(f"⚠️ High memory usage: {memory_usage}%")
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Resource monitoring error: {e}")
                time.sleep(60)
    
    # Start monitoring in background
    monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
    monitor_thread.start()

def get_recommended_settings():
    """Get recommended settings based on system capabilities"""
    try:
        info = get_system_info()
        cpu_cores = info['cpu']['cores']
        memory_gb = info['memory']['total_gb']
        
        # Adjust settings based on hardware
        if cpu_cores >= 8 and memory_gb >= 16:
            return {
                'detection_interval': 120,
                'confidence_threshold': 0.6,
                'max_concurrent_cameras': 4,
                'frame_rate': 15
            }
        elif cpu_cores >= 4 and memory_gb >= 8:
            return {
                'detection_interval': 180,
                'confidence_threshold': 0.65,
                'max_concurrent_cameras': 2,
                'frame_rate': 10
            }
        else:
            return {
                'detection_interval': 300,
                'confidence_threshold': 0.7,
                'max_concurrent_cameras': 1,
                'frame_rate': 5
            }
            
    except Exception as e:
        print(f"❌ Settings recommendation error: {e}")
        return {
            'detection_interval': 240,
            'confidence_threshold': 0.65,
            'max_concurrent_cameras': 1,
            'frame_rate': 10
        }

# Initialize resource monitoring on import
monitor_resource_usage()