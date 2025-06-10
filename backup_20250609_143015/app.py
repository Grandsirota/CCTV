# app.py - CPU Optimized Version

import os
import time
from datetime import datetime
from flask import Flask, Response, render_template, request, jsonify, send_from_directory
import threading
import gc
from camera import OptimizedCameraSystem
from db import Database
from utils import ensure_dirs

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "detection_data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LOG_DIR = os.path.join(DATA_DIR, "logs")

ensure_dirs([DATA_DIR, IMAGES_DIR, LOG_DIR])

# Flask app with optimized settings
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300  # Cache static files for 5 minutes
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False  # Reduce JSON overhead

# Optimized RTSP cameras
rtsp_cameras = {
    "Front Gate Camera": "rtsp://rsrc2:rsrc1234@7dd608e038a9.sn.mynetname.net/chID=9&streamType=sub",  # Use sub stream
    "Main Entrance": "rtsp://rsrc2:rsrc1234@7dd608e038a9.sn.mynetname.net/chID=2&streamType=sub", 
    "Parking Area": "rtsp://rsrc2:rsrc1234@608905d16e93.sn.mynetname.net/chID=1&streamType=sub",
    "Lobby Camera": "rtsp://rsrc2:rsrc1234@608905d16e93.sn.mynetname.net/chID=2&streamType=sub"
}

# CPU optimized settings
DETECTION_SETTINGS = {
    'confidence_threshold': 0.65,  # Slightly higher to reduce false positives
    'detection_interval': 240,     # 4 minutes to reduce processing
    'frame_rate': 10,              # Lower frame rate
    'enable_notifications': True,
    'save_images': True,
    'telegram_token': '7687849270:AAG5YgRP64KM13hbjZKFTPgA29DUXbm3ens',
    'telegram_chat_id': '-4809459710',
    'flask_host': 'http://localhost:5000',
    'max_concurrent_detections': 2  # Limit concurrent processing
}

# Initialize systems
camera_system = OptimizedCameraSystem(rtsp_cameras, IMAGES_DIR, DETECTION_SETTINGS)
db = Database(host="localhost", user="root", password="", database="detect_db")

# Global variables
active_camera = list(rtsp_cameras.keys())[0]
last_system_stats_time = 0
cached_system_stats = {}

@app.route('/')
def index():
    """Main page with cached template"""
    return render_template('index.html', 
                         cameras=list(rtsp_cameras.keys()),
                         settings=DETECTION_SETTINGS)

@app.route('/video_feed')
def video_feed():
    """Optimized video streaming"""
    camera_id = request.args.get('camera_id', active_camera)
    
    def generate():
        last_frame_time = 0
        frame_interval = 1.0 / 15  # 15 FPS max for web streaming
        
        while True:
            current_time = time.time()
            
            # Limit frame rate for web streaming
            if current_time - last_frame_time < frame_interval:
                time.sleep(0.01)
                continue
            
            frame_bytes = camera_system.get_jpeg(camera_id)
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                last_frame_time = current_time
            else:
                time.sleep(0.1)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/switch_camera/<camera_id>')
def switch_camera(camera_id):
    """Switch active camera"""
    global active_camera
    if camera_id in camera_system.cameras:
        active_camera = camera_id
        return jsonify({"status": "success", "message": f"Switched to {camera_id}"})
    return jsonify({"status": "error", "message": "Camera not found"})

@app.route('/get_all_detections')
def get_all_detections():
    """Get detections with caching"""
    try:
        total_counts = db.get_total_counts()
        recent_all = db.get_recent_detections_all(limit=20)  # Reduced limit

        # Convert datetime objects to ISO format
        for det in recent_all:
            if isinstance(det["timestamp"], datetime):
                det["timestamp"] = det["timestamp"].isoformat()
            if isinstance(det.get("created_at"), datetime):
                det["created_at"] = det["created_at"].isoformat()

        return jsonify({
            "total_counts": total_counts,
            "recent_detections": recent_all
        })
    except Exception as e:
        print(f"Error getting detections: {e}")
        return jsonify({"total_counts": {}, "recent_detections": []})

@app.route('/image/<path:image_path>')
def serve_image(image_path):
    """Serve images with caching"""
    directory = os.path.dirname(image_path)
    filename = os.path.basename(image_path)
    
    response = send_from_directory(os.path.join(IMAGES_DIR, directory), filename)
    response.cache_control.max_age = 3600  # Cache for 1 hour
    return response

@app.route('/export_csv')
def export_csv():
    """Export with streaming response for large datasets"""
    import csv
    from io import StringIO
    
    try:
        all_detections = db.get_all_detections()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Camera', 'Timestamp', 'Confidence', 'Image Path'])
        
        for detection in all_detections:
            writer.writerow([
                detection['id'],
                detection['camera_id'],
                detection['timestamp'],
                detection['confidence'],
                detection.get('image_path', '')
            ])
        
        output.seek(0)
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=detections_{datetime.now().strftime("%Y%m%d")}.csv'
            }
        )
    except Exception as e:
        print(f"Export error: {e}")
        return jsonify({"error": "Export failed"}), 500

@app.route('/start_all_cameras')
def start_all_cameras():
    """Start all cameras"""
    try:
        camera_system.start_all()
        return jsonify({"status": "success", "message": "All cameras started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/get_system_stats')
def get_system_stats():
    """Get system stats with caching to reduce CPU overhead"""
    global last_system_stats_time, cached_system_stats
    
    current_time = time.time()
    
    # Cache system stats for 5 seconds to reduce psutil calls
    if current_time - last_system_stats_time < 5:
        return jsonify(cached_system_stats)
    
    try:
        import psutil
        
        # Get stats less frequently to reduce overhead
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Shorter interval
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        stats = {
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "disk_percent": round(disk.percent, 1),
            "active_cameras": len([cam for cam in camera_system.cameras.values() if cam.running]),
            "total_cameras": len(camera_system.cameras),
            "uptime": round(current_time - camera_system.start_time, 0)
        }
        
        cached_system_stats = stats
        last_system_stats_time = current_time
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"System stats error: {e}")
        return jsonify({
            "cpu_percent": 0,
            "memory_percent": 0, 
            "disk_percent": 0,
            "active_cameras": 0,
            "total_cameras": len(rtsp_cameras),
            "uptime": 0
        })

@app.route('/update_detection', methods=['POST'])
def update_detection():
    """Optimized detection update"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data"}), 400

        # Use thread pool for database operations to avoid blocking
        def save_detection():
            try:
                db.add_detection(
                    camera_id=data['camera_id'],
                    timestamp=datetime.now().isoformat(),
                    confidence=data['confidence'],
                    image_path=data.get('image_path', '')
                )
            except Exception as e:
                print(f"DB save error: {e}")

        # Execute in background thread
        threading.Thread(target=save_detection, daemon=True).start()
        
        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"Update detection error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_detection', methods=['DELETE'])
def delete_detection():
    """Delete detection with optimized query"""
    detection_id = request.args.get('id', type=int)
    if detection_id is None:
        return jsonify({'status': 'error', 'message': 'Missing ID'}), 400

    try:
        # Use background thread for deletion
        def delete_async():
            try:
                db._connect()
                db.cursor.execute("DELETE FROM detections WHERE id = %s", (detection_id,))
                db.conn.commit()
                db._disconnect()
            except Exception as e:
                print(f"Delete error: {e}")

        threading.Thread(target=delete_async, daemon=True).start()
        return jsonify({'status': 'success'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health')
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "cameras_running": len([c for c in camera_system.cameras.values() if c.running]),
        "uptime": time.time() - camera_system.start_time
    })

# Cleanup function
def cleanup_resources():
    """Periodic cleanup to maintain performance"""
    def cleanup_worker():
        while True:
            try:
                time.sleep(600)  # Every 10 minutes
                gc.collect()  # Force garbage collection
                print("🧹 Performed app cleanup")
            except Exception as e:
                print(f"Cleanup error: {e}")
                time.sleep(60)
    
    threading.Thread(target=cleanup_worker, daemon=True).start()

if __name__ == '__main__':
    try:
        print("🚀 Starting NT Telecom Optimized Detection System...")
        print(f"🔧 CPU Optimized Settings: {DETECTION_SETTINGS}")
        
        # Initialize database
        db.initialize()
        
        # Start cleanup thread
        cleanup_resources()
        
        # Set start time
        camera_system.start_time = time.time()
        
        # Start cameras
        camera_system.start_all()
        
        print("✅ System running at http://localhost:5000")
        print("💡 Optimized for low CPU usage")
        
        # Run with optimized settings
        app.run(
            host='0.0.0.0', 
            port=5000, 
            threaded=True, 
            debug=False,
            use_reloader=False  # Disable reloader to save memory
        )
        
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        camera_system.stop_all()
    except Exception as e:
        print(f"❌ Error: {e}")
        camera_system.stop_all()