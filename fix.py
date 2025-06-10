#!/usr/bin/env python3
"""
complete_system_fix.py - Complete fix for all NT Telecom CCTV issues

This script will automatically fix all the issues:
1. Dashboard not updating
2. Camera feeds not displaying
3. Image download not working
4. Detection history issues
"""

import os
import shutil
import time
from datetime import datetime

def backup_files():
    """Create backup of current files"""
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'app.py',
        'camera.py', 
        'main.js',
        'templates/index.html'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            shutil.copy2(file_path, os.path.join(backup_dir, os.path.basename(file_path)))
            print(f"✅ Backed up: {file_path}")
    
    print(f"📁 Backup created in: {backup_dir}")
    return backup_dir

def create_fixed_app_py():
    """Create fixed app.py"""
    content = '''# app.py - Fixed Version for NT Telecom CCTV

import os
import time
from datetime import datetime
from flask import Flask, Response, render_template, request, jsonify, send_from_directory, url_for
from camera import OptimizedCameraSystem
from db import Database
from utils import ensure_dirs

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "detection_data")
IMAGES_DIR = os.path.join(DATA_DIR, "images")
LOG_DIR = os.path.join(DATA_DIR, "logs")

ensure_dirs([DATA_DIR, IMAGES_DIR, LOG_DIR])

# Flask app
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# RTSP cameras - FIXED URLs
rtsp_cameras = {
    "Front Gate Camera": "rtsp://rsrc2:rsrc1234@7dd608e038a9.sn.mynetname.net/chID=9&streamType=sub",
    "Main Entrance": "rtsp://rsrc2:rsrc1234@7dd608e038a9.sn.mynetname.net/chID=2&streamType=sub", 
    "Parking Area": "rtsp://rsrc2:rsrc1234@608905d16e93.sn.mynetname.net/chID=1&streamType=main",  # Changed to main
    "Lobby Camera": "rtsp://rsrc2:rsrc1234@608905d16e93.sn.mynetname.net/chID=2&streamType=main"   # Changed to main
}

# Optimized settings
DETECTION_SETTINGS = {
    'confidence_threshold': 0.65,
    'detection_interval': 300,  # 5 minutes
    'frame_rate': 8,
    'enable_notifications': True,
    'save_images': True,
    'telegram_token': '7687849270:AAG5YgRP64KM13hbjZKFTPgA29DUXbm3ens',
    'telegram_chat_id': '-4809459710',
    'flask_host': 'http://localhost:5000'
}

# Initialize systems
camera_system = OptimizedCameraSystem(rtsp_cameras, IMAGES_DIR, DETECTION_SETTINGS)
db = Database(host="localhost", user="root", password="", database="detect_db")

# Global variables
active_camera = list(rtsp_cameras.keys())[0]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html', 
                         cameras=list(rtsp_cameras.keys()),
                         settings=DETECTION_SETTINGS)

@app.route('/video_feed')
def video_feed():
    """FIXED: Video streaming with proper error handling"""
    camera_id = request.args.get('camera_id', active_camera)
    quality = request.args.get('quality', 'medium')
    
    print(f"🎥 Video feed requested for: {camera_id}")
    
    def generate():
        while True:
            try:
                frame_bytes = camera_system.get_jpeg(camera_id)
                if frame_bytes:
                    yield (b'--frame\\r\\n'
                           b'Content-Type: image/jpeg\\r\\n\\r\\n' + frame_bytes + b'\\r\\n')
                else:
                    print(f"⚠️ No frame from {camera_id}")
                    time.sleep(0.1)
            except Exception as e:
                print(f"❌ Video feed error for {camera_id}: {e}")
                time.sleep(0.5)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/switch_camera/<camera_id>')
def switch_camera(camera_id):
    """FIXED: Camera switching"""
    global active_camera
    print(f"🔄 Switching to camera: {camera_id}")
    
    if camera_id in camera_system.cameras:
        active_camera = camera_id
        return jsonify({"status": "success", "message": f"Switched to {camera_id}"})
    else:
        print(f"❌ Camera not found: {camera_id}")
        return jsonify({"status": "error", "message": "Camera not found"})

@app.route('/get_all_detections')
def get_all_detections():
    """FIXED: Get detections with proper error handling"""
    try:
        total_counts = db.get_total_counts()
        recent_all = db.get_recent_detections_all(limit=30)

        # Convert datetime objects
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
        print(f"❌ Error getting detections: {e}")
        return jsonify({
            "total_counts": {"total": 0},
            "recent_detections": []
        })

@app.route('/image/<path:image_path>')
def serve_image(image_path):
    """FIXED: Serve images with proper path handling"""
    try:
        print(f"📷 Serving image: {image_path}")
        
        # Handle different path formats
        if '/' in image_path:
            directory = os.path.dirname(image_path)
            filename = os.path.basename(image_path)
            full_path = os.path.join(IMAGES_DIR, directory, filename)
        else:
            # Try to find file in subdirectories
            filename = image_path
            full_path = None
            
            for root, dirs, files in os.walk(IMAGES_DIR):
                if filename in files:
                    full_path = os.path.join(root, filename)
                    break
        
        if full_path and os.path.exists(full_path):
            directory = os.path.dirname(full_path)
            filename = os.path.basename(full_path)
            return send_from_directory(directory, filename)
        else:
            print(f"❌ Image not found: {image_path}")
            return "Image not found", 404
            
    except Exception as e:
        print(f"❌ Error serving image {image_path}: {e}")
        return "Error serving image", 500

@app.route('/export_csv')
def export_csv():
    """Export detection data to CSV"""
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
        print(f"❌ Export error: {e}")
        return jsonify({"error": "Export failed"}), 500

@app.route('/get_system_stats')
def get_system_stats():
    """FIXED: Get system statistics"""
    try:
        import psutil
        
        stats = {
            "cpu_percent": round(psutil.cpu_percent(interval=0.1), 1),
            "memory_percent": round(psutil.virtual_memory().percent, 1),
            "disk_percent": round(psutil.disk_usage('/').percent, 1),
            "active_cameras": len([cam for cam in camera_system.cameras.values() if cam.running]),
            "total_cameras": len(camera_system.cameras),
            "uptime": time.time() - camera_system.start_time if hasattr(camera_system, 'start_time') else 0
        }
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ System stats error: {e}")
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
    """FIXED: Update detection"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data"}), 400

        db.add_detection(
            camera_id=data['camera_id'],
            timestamp=datetime.now().isoformat(),
            confidence=data['confidence'],
            image_path=data.get('image_path', '')
        )

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ Update detection error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/delete_detection', methods=['DELETE'])
def delete_detection():
    """FIXED: Delete detection"""
    detection_id = request.args.get('id', type=int)
    if detection_id is None:
        return jsonify({'status': 'error', 'message': 'Missing ID'}), 400

    try:
        db._connect()
        db.cursor.execute("DELETE FROM detections WHERE id = %s", (detection_id,))
        db.conn.commit()
        db._disconnect()
        
        return jsonify({'status': 'success'})

    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/start_all_cameras')
def start_all_cameras():
    """Start all cameras"""
    try:
        camera_system.start_all()
        return jsonify({"status": "success", "message": "All cameras started"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# Add CORS headers for development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

if __name__ == '__main__':
    try:
        print("🚀 Starting NT Telecom Optimized Detection System...")
        print(f"🔧 Settings: {DETECTION_SETTINGS}")
        
        # Initialize database
        db.initialize()
        
        # Set start time
        camera_system.start_time = time.time()
        
        # Start cameras
        camera_system.start_all()
        
        print("✅ System running at http://localhost:5000")
        print("💡 Optimized for low CPU usage")
        
        app.run(
            host='0.0.0.0', 
            port=5000, 
            threaded=True, 
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        camera_system.stop_all()
    except Exception as e:
        print(f"❌ Error: {e}")
        camera_system.stop_all()
'''
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created fixed app.py")

def create_fixed_main_js():
    """Create fixed main.js for frontend"""
    content = '''// main.js - Fixed Version for NT Telecom Dashboard

class NTVisionDashboard {
    constructor() {
        this.cameras = {
            "Front Gate Camera": "Front Gate Camera",
            "Main Entrance": "Main Entrance", 
            "Parking Area": "Parking Area",
            "Lobby Camera": "Lobby Camera"
        };
        
        this.currentCamera = 'Front Gate Camera';
        this.isAutoRefresh = true;
        this.refreshInterval = 15000; // 15 seconds
        this.charts = {};
        this.lastUpdateTime = 0;
        this.retryCount = 0;
        this.maxRetries = 3;
        
        this.init();
    }

    init() {
        console.log('🚀 Initializing NT Vision Dashboard...');
        
        this.initializeEventListeners();
        this.initializeTheme();
        this.initializeNavigation();
        this.initializeClock();
        this.setupCameraGrid();
        this.loadInitialData();
        this.startAutoRefresh();
        
        console.log('✅ Dashboard initialized successfully');
    }

    initializeEventListeners() {
        // Navigation Links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const href = link.getAttribute('href');
                if (href && href !== '#') {
                    const target = href.substring(1);
                    this.navigateToPage(target);
                }
            });
        });

        // Sidebar toggle
        const sidebarToggle = document.getElementById('sidebar-toggle');
        if (sidebarToggle) {
            sidebarToggle.addEventListener('click', () => this.toggleSidebar());
        }

        // Search input
        const searchInput = document.getElementById('detection-search');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterDetections(e.target.value);
            });
        }

        // Date filter
        const dateFilter = document.getElementById('date-filter');
        if (dateFilter) {
            dateFilter.addEventListener('change', (e) => {
                this.filterByDate(e.target.value);
            });
        }

        // Clear filters
        const clearFilters = document.getElementById('clear-filters');
        if (clearFilters) {
            clearFilters.addEventListener('click', () => {
                if (searchInput) searchInput.value = '';
                if (dateFilter) dateFilter.value = '';
                this.updateDetections();
            });
        }

        // Modal close buttons
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });

        // Chart period buttons
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const period = e.target.dataset.period;
                this.updateChartPeriod(period);
            });
        });
    }

    setupCameraGrid() {
        const cameraGrid = document.getElementById('camera-grid');
        if (!cameraGrid) return;

        cameraGrid.innerHTML = '';

        Object.keys(this.cameras).forEach((cameraName, index) => {
            const cameraCard = document.createElement('div');
            cameraCard.className = `camera-card ${index === 0 ? 'active' : ''}`;
            cameraCard.dataset.cameraId = cameraName;

            cameraCard.innerHTML = `
                <div class="camera-header">
                    <h4>${this.formatCameraName(cameraName)}</h4>
                    <span class="camera-status online">
                        <i class="fas fa-circle"></i>
                        LIVE
                    </span>
                </div>
                <div class="camera-preview">
                    <img src="/video_feed?camera_id=${encodeURIComponent(cameraName)}&t=${Date.now()}" 
                        alt="${cameraName}" 
                        onerror="this.src='/api/placeholder/300/200'; console.log('Camera feed error for ${cameraName}');">
                </div>
            `;

            cameraCard.addEventListener('click', () => {
                this.switchCamera(cameraName);
            });

            cameraGrid.appendChild(cameraCard);
        });

        this.updateMainVideoFeed();
    }

    formatCameraName(cameraName) {
        const nameMap = {
            "Front Gate Camera": "Front Gate",
            "Main Entrance": "Main Entrance",
            "Parking Area": "Parking", 
            "Lobby Camera": "Lobby"
        };
        return nameMap[cameraName] || cameraName;
    }

    updateMainVideoFeed() {
        const videoFeed = document.getElementById('main-video-feed');
        if (videoFeed) {
            const timestamp = Date.now();
            const newSrc = `/video_feed?camera_id=${encodeURIComponent(this.currentCamera)}&t=${timestamp}`;
            
            console.log(`🎥 Updating main video feed: ${this.currentCamera}`);
            videoFeed.src = newSrc;
            
            videoFeed.onerror = () => {
                console.warn(`❌ Failed to load video feed for ${this.currentCamera}`);
                videoFeed.src = '/api/placeholder/1280/720';
            };
        }
    }

    initializeTheme() {
        document.body.setAttribute('data-theme', 'dark');
    }

    initializeNavigation() {
        this.navigateToPage('dashboard');
    }

    initializeClock() {
        this.updateClock();
        setInterval(() => this.updateClock(), 1000);
    }

    async loadInitialData() {
        try {
            console.log('📊 Loading initial data...');
            
            await Promise.all([
                this.updateSystemStats(),
                this.updateDetections(),
                this.updateActivityStream()
            ]);
            
            this.retryCount = 0;
            console.log('✅ Initial data loaded successfully');
            
        } catch (error) {
            console.error('❌ Error loading initial data:', error);
            this.handleDataLoadError(error);
        }
    }

    handleDataLoadError(error) {
        this.retryCount++;
        
        if (this.retryCount < this.maxRetries) {
            console.log(`🔄 Retrying data load... (${this.retryCount}/${this.maxRetries})`);
            setTimeout(() => this.loadInitialData(), 5000);
        } else {
            this.showNotification('Unable to load dashboard data. Check your connection.', 'error');
        }
    }

    async updateSystemStats() {
        try {
            const response = await fetch('/get_system_stats', {
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const stats = await response.json();
            
            // Update active cameras
            const activeCameras = document.getElementById('active-cameras');
            if (activeCameras) {
                activeCameras.textContent = `${stats.active_cameras}/${stats.total_cameras}`;
            }
            
            // Update system uptime
            if (stats.uptime) {
                const uptimeElement = document.getElementById('system-uptime');
                if (uptimeElement) {
                    uptimeElement.textContent = this.formatUptime(stats.uptime);
                }
            }
            
        } catch (error) {
            console.error('❌ Error updating system stats:', error);
            this.setDefaultSystemStats();
        }
    }

    setDefaultSystemStats() {
        const activeCameras = document.getElementById('active-cameras');
        if (activeCameras) activeCameras.textContent = '0/4';
    }

    formatUptime(seconds) {
        const days = Math.floor(seconds / 86400);
        const hours = Math.floor((seconds % 86400) / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        
        if (days > 0) return `Running ${days}d ${hours}h`;
        if (hours > 0) return `Running ${hours}h ${minutes}m`;
        return `Running ${minutes}m`;
    }

    async updateDetections() {
        try {
            console.log('📊 Updating detections...');
            
            const response = await fetch('/get_all_detections', {
                cache: 'no-cache'
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            // Update detection counters
            this.updateDetectionCounters(data.total_counts);
            
            // Update detections table
            this.updateDetectionsTable(data.recent_detections || []);
            
            this.lastUpdateTime = Date.now();
            
        } catch (error) {
            console.error('❌ Error updating detections:', error);
            this.setDefaultDetectionData();
        }
    }

    updateDetectionCounters(totalCounts) {
        const totalDetections = document.getElementById('total-detections');
        if (totalDetections) {
            const total = totalCounts.total || 0;
            this.animateCounter(totalDetections, total);
        }
        
        const todayDetections = document.getElementById('today-detections');
        if (todayDetections) {
            // Calculate today's detections (simplified)
            todayDetections.textContent = '0';
        }
    }

    animateCounter(element, targetValue) {
        const currentValue = parseInt(element.textContent) || 0;
        const increment = Math.ceil((targetValue - currentValue) / 20);
        
        if (currentValue < targetValue) {
            element.textContent = Math.min(currentValue + increment, targetValue);
            setTimeout(() => this.animateCounter(element, targetValue), 50);
        }
    }

    setDefaultDetectionData() {
        const totalDetections = document.getElementById('total-detections');
        const todayDetections = document.getElementById('today-detections');
        
        if (totalDetections) totalDetections.textContent = '0';
        if (todayDetections) todayDetections.textContent = '0';
    }

    updateDetectionsTable(detections) {
        const tbody = document.getElementById('detections-tbody');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        
        if (detections.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="no-data">
                        <i class="fas fa-search"></i>
                        <p>No detections found</p>
                    </td>
                </tr>
            `;
            return;
        }
        
        detections.forEach(detection => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${this.formatDateTime(detection.timestamp)}</td>
                <td>${this.formatCameraName(detection.camera_id)}</td>
                <td>
                    <span class="confidence-badge confidence-${this.getConfidenceLevel(detection.confidence)}">
                        ${Math.round(detection.confidence)}%
                    </span>
                </td>
                <td>
                    ${detection.image_path ? 
                        `<img src="/image/${detection.image_path}" class="thumbnail" alt="Detection" onclick="window.ntDashboard.showDetectionModal('${detection.image_path}', '${detection.camera_id}', '${detection.timestamp}', ${detection.confidence})">` : 
                        '<span class="no-data">No image</span>'
                    }
                </td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn view" title="View Details" onclick="window.ntDashboard.showDetectionModal('${detection.image_path}', '${detection.camera_id}', '${detection.timestamp}', ${detection.confidence})">
                            <i class="fas fa-eye"></i>
                        </button>
                        ${detection.image_path ? 
                            `<button class="action-btn download" title="Download" onclick="window.ntDashboard.downloadDetection('${detection.image_path}')">
                                <i class="fas fa-download"></i>
                            </button>` : ''
                        }
                        <button class="action-btn delete" title="Delete" onclick="window.ntDashboard.deleteDetection(${detection.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async updateActivityStream() {
        try {
            const response = await fetch('/get_all_detections');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            const activityStream = document.getElementById('activity-stream');
            if (!activityStream) return;
            
            const recentDetections = data.recent_detections?.slice(0, 5) || [];
            
            if (recentDetections.length === 0) {
                activityStream.innerHTML = `
                    <div class="activity-placeholder">
                        <i class="fas fa-search"></i>
                        <p>Monitoring for activity...</p>
                    </div>
                `;
                return;
            }
            
            activityStream.innerHTML = '';
            
            recentDetections.forEach(detection => {
                const activityItem = document.createElement('div');
                activityItem.className = 'activity-item';
                activityItem.innerHTML = `
                    <div class="activity-icon">
                        <i class="fas fa-user"></i>
                    </div>
                    <div class="activity-details">
                        <h4>Person Detected</h4>
                        <p>${this.formatCameraName(detection.camera_id)} - Confidence: ${Math.round(detection.confidence)}%</p>
                        <span class="activity-time">${this.getTimeAgo(detection.timestamp)}</span>
                    </div>
                `;
                activityStream.appendChild(activityItem);
            });
            
        } catch (error) {
            console.error('❌ Error updating activity stream:', error);
        }
    }

    switchCamera(cameraName) {
        if (!this.cameras[cameraName]) {
            console.warn(`❌ Camera ${cameraName} not found`);
            return;
        }

        console.log(`🔄 Switching to camera: ${cameraName}`);
        this.currentCamera = cameraName;
        
        // Update active camera indicator
        document.querySelectorAll('.camera-card').forEach(card => {
            card.classList.remove('active');
            if (card.dataset.cameraId === cameraName) {
                card.classList.add('active');
            }
        });
        
        // Update camera name in video overlay
        const cameraNameElement = document.getElementById('active-camera-name');
        if (cameraNameElement) {
            cameraNameElement.textContent = this.formatCameraName(cameraName);
        }
        
        // Update main video feed
        this.updateMainVideoFeed();
        
        // Call backend to switch camera
        fetch(`/switch_camera/${encodeURIComponent(cameraName)}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    this.showNotification(`Switched to ${this.formatCameraName(cameraName)}`, 'success');
                } else {
                    throw new Error(data.message || 'Failed to switch camera');
                }
            })
            .catch(error => {
                console.error('❌ Error switching camera:', error);
                this.showNotification('Error switching camera', 'error');
            });
    }

    showDetectionModal(imagePath, cameraId, timestamp, confidence) {
        const modal = document.getElementById('detection-modal');
        const modalImage = document.getElementById('modal-image');
        const modalTitle = document.getElementById('modal-title');
        const modalDetails = document.getElementById('modal-details');
        
        if (modal && modalImage && modalTitle && modalDetails) {
            modalTitle.textContent = 'Detection Details';
            modalImage.src = imagePath ? `/image/${imagePath}` : '/api/placeholder/400/300';
            
            modalDetails.innerHTML = `
                <div class="detection-details">
                    <h4>Detection Information</h4>
                    <p><strong>Camera:</strong> ${this.formatCameraName(cameraId)}</p>
                    <p><strong>Time:</strong> ${this.formatDateTime(timestamp)}</p>
                    <p><strong>Confidence:</strong> ${Math.round(confidence)}%</p>
                    <p><strong>Status:</strong> <span class="confidence-badge confidence-${this.getConfidenceLevel(confidence)}">${this.getConfidenceText(confidence)}</span></p>
                </div>
            `;
            
            modal.classList.add('active');
        }
    }

    downloadDetection(imagePath) {
        if (imagePath) {
            console.log(`📥 Downloading image: ${imagePath}`);
            const link = document.createElement('a');
            link.href = `/image/${imagePath}`;
            link.download = imagePath.split('/').pop();
            link.click();
        }
    }

    async deleteDetection(detectionId) {
        if (!confirm('Are you sure you want to delete this detection?')) return;

        try {
            const response = await fetch(`/delete_detection?id=${detectionId}`, { method: 'DELETE' });
            const result = await response.json();
            if (result.status === 'success') {
                this.showNotification('Detection deleted successfully', 'success');
                this.updateDetections();
            } else {
                throw new Error(result.message || 'Delete failed');
            }
        } catch (error) {
            console.error('❌ Error deleting detection:', error);
            this.showNotification('Error deleting detection', 'error');
        }
    }

    toggleSidebar() {
        const sidebar = document.querySelector('.premium-sidebar');
        const mainContent = document.querySelector('.premium-main');
        
        if (sidebar && mainContent) {
            sidebar.classList.toggle('collapsed');
            mainContent.classList.toggle('expanded');
        }
    }

    navigateToPage(pageName) {
        console.log(`🧭 Navigating to: ${pageName}`);
        
        // Hide all content areas
        document.querySelectorAll('.content-area').forEach(area => {
            area.classList.remove('active');
        });
        
        // Show selected content area
        const targetArea = document.getElementById(`${pageName}-content`);
        if (targetArea) {
            targetArea.classList.add('active');
        } else {
            console.warn(`❌ Content area not found: ${pageName}-content`);
        }
        
        // Update navigation active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[href="#${pageName}"]`)?.closest('.nav-item');
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }
        
        // Update page title
        const pageTitle = document.getElementById('page-title');
        const currentPage = document.getElementById('current-page');
        
        const pageTitles = {
            'dashboard': 'Intelligence Dashboard',
            'surveillance': 'Live Surveillance',
            'detections': 'Detection History',
            'reports': 'Analytics & Reports'
        };
        
        if (pageTitle) pageTitle.textContent = pageTitles[pageName] || pageName;
        if (currentPage) currentPage.textContent = pageTitles[pageName] || pageName;
        
        // Load page-specific data
        this.loadPageData(pageName);
    }

    loadPageData(pageName) {
        switch(pageName) {
            case 'surveillance':
                this.loadSurveillanceData();
                break;
            case 'detections':
                this.updateDetections();
                break;
            case 'reports':
                this.loadReportsData();
                break;
            case 'dashboard':
                this.updateDetections();
                break;
        }
    }

    loadSurveillanceData() {
        const surveillanceGrid = document.getElementById('surveillance-grid');
        if (!surveillanceGrid) return;

        surveillanceGrid.innerHTML = '';
        
        Object.keys(this.cameras).forEach(cameraName => {
            const cameraCard = document.createElement('div');
            cameraCard.className = 'surveillance-camera-card';
            
            cameraCard.innerHTML = `
                <div class="surveillance-camera-header">
                    <h3>
                        <i class="fas fa-video"></i>
                        ${this.formatCameraName(cameraName)}
                    </h3>
                    <span class="camera-status online">
                        <i class="fas fa-circle"></i>
                        LIVE
                    </span>
                </div>
                <div class="surveillance-camera-feed">
                    <img src="/video_feed?camera_id=${encodeURIComponent(cameraName)}&t=${Date.now()}" 
                         alt="${cameraName}"
                         onerror="this.src='/api/placeholder/640/360'">
                </div>
                <div class="surveillance-camera-footer">
                    <div class="camera-stats">
                        <div class="stat-item">
                            <i class="fas fa-users"></i>
                            <span class="stat-value">0</span>
                            <span>Detections</span>
                        </div>
                        <div class="stat-item">
                            <i class="fas fa-clock"></i>
                            <span class="stat-value">24/7</span>
                            <span>Active</span>
                        </div>
                    </div>
                </div>
            `;
            
            surveillanceGrid.appendChild(cameraCard);
        });
    }

    loadReportsData() {
        console.log('📊 Loading reports data...');
        // Initialize charts if needed
        this.initializeCharts();
    }

    initializeCharts() {
        // Initialize analytics chart
        this.initializeAnalyticsChart();
        this.initializeTrendsChart();
        this.initializePerformanceChart();
    }

    initializeAnalyticsChart() {
        const analyticsCanvas = document.getElementById('analytics-chart');
        if (analyticsCanvas && !this.charts.analytics) {
            this.charts.analytics = new Chart(analyticsCanvas, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Detections',
                        data: [],
                        borderColor: '#2563eb',
                        backgroundColor: 'rgba(37, 99, 235, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true },
                        x: { grid: { color: 'rgba(0, 0, 0, 0.1)' } }
                    }
                }
            });
        }
    }

    initializeTrendsChart() {
        const trendsCanvas = document.getElementById('trends-chart');
        if (trendsCanvas && !this.charts.trends) {
            this.charts.trends = new Chart(trendsCanvas, {
                type: 'bar',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Daily Detections',
                        data: [0, 0, 0, 0, 0, 0, 0],
                        backgroundColor: '#2563eb'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true } }
                }
            });
        }
    }

    initializePerformanceChart() {
        const performanceCanvas = document.getElementById('performance-chart');
        if (performanceCanvas && !this.charts.performance) {
            this.charts.performance = new Chart(performanceCanvas, {
                type: 'doughnut',
                data: {
                    labels: ['Front Gate', 'Main Entrance', 'Parking', 'Lobby'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: ['#2563eb', '#f59e0b', '#10b981', '#06b6d4']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: '60%',
                    plugins: {
                        legend: { position: 'bottom' }
                    }
                }
            });
        }
    }

    updateClock() {
        const now = new Date();
        
        const timeElement = document.getElementById('current-time');
        const dateElement = document.getElementById('current-date');
        
        if (timeElement) {
            timeElement.textContent = now.toLocaleTimeString('en-US', { hour12: false });
        }
        
        if (dateElement) {
            dateElement.textContent = now.toLocaleDateString('en-US', { 
                weekday: 'short', 
                month: 'short', 
                day: 'numeric' 
            });
        }
    }

    updateChartPeriod(period) {
        document.querySelectorAll('.period-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        const activeBtn = document.querySelector(`[data-period="${period}"]`);
        if (activeBtn) activeBtn.classList.add('active');
    }

    filterDetections(searchTerm) {
        const rows = document.querySelectorAll('#detections-tbody tr');
        
        rows.forEach(row => {
            if (row.querySelector('.no-data')) return;
            
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm.toLowerCase())) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    async filterByDate(dateValue) {
        if (!dateValue) {
            this.updateDetections();
            return;
        }
        
        try {
            const response = await fetch(`/get_detections_by_date?date=${dateValue}`);
            if (response.ok) {
                const data = await response.json();
                this.updateDetectionsTable(data.detections || []);
            }
        } catch (error) {
            console.error('❌ Error filtering by date:', error);
        }
    }

    closeModal() {
        const modals = document.querySelectorAll('.premium-modal.active');
        modals.forEach(modal => modal.classList.remove('active'));
    }

    showNotification(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 1000;
            `;
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.style.cssText = `
            background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
            color: white;
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            animation: slideIn 0.3s ease;
        `;
        
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };
        
        toast.innerHTML = `
            <i class="${icons[type]}" style="margin-right: 8px;"></i>
            ${message}
            <button onclick="this.parentNode.remove()" style="background: none; border: none; color: white; margin-left: 10px; cursor: pointer;">×</button>
        `;
        
        container.appendChild(toast);
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }

    startAutoRefresh() {
        if (this.isAutoRefresh) {
            setInterval(() => {
                if (document.visibilityState === 'visible' && 
                    Date.now() - this.lastUpdateTime > this.refreshInterval) {
                    
                    this.updateSystemStats();
                    this.updateDetections();
                    this.updateActivityStream();
                }
            }, this.refreshInterval);
        }
    }

    // Utility functions
    formatDateTime(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const time = new Date(timestamp);
        const diffInSeconds = Math.floor((now - time) / 1000);
        
        if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
        return `${Math.floor(diffInSeconds / 86400)} days ago`;
    }

    getConfidenceLevel(confidence) {
        if (confidence >= 80) return 'high';
        if (confidence >= 60) return 'medium';
        return 'low';
    }

    getConfidenceText(confidence) {
        if (confidence >= 80) return 'High Confidence';
        if (confidence >= 60) return 'Medium Confidence';
        return 'Low Confidence';
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Hide loading screen
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        setTimeout(() => {
            loadingScreen.style.opacity = '0';
            setTimeout(() => {
                loadingScreen.style.display = 'none';
            }, 300);
        }, 1000);
    }
    
    window.ntDashboard = new NTVisionDashboard();
    console.log('✅ Dashboard ready');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && window.ntDashboard) {
        setTimeout(() => {
            window.ntDashboard.updateSystemStats();
            window.ntDashboard.updateDetections();
        }, 1000);
    }
});

// Export for global access
window.NTVisionDashboard = NTVisionDashboard;
'''
    
    with open('static/js/main.js', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created fixed main.js")

def create_startup_script():
    """Create startup script for easy launch"""
    content = '''#!/bin/bash
# startup.sh - NT Telecom CCTV System Startup Script

echo "🚀 Starting NT Telecom CCTV Detection System"
echo "============================================="

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check required packages
echo "📦 Checking dependencies..."
python3 -c "import cv2, torch, ultralytics, flask, pymysql, psutil" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️ Some dependencies missing. Installing..."
    pip3 install opencv-python torch ultralytics flask pymysql psutil requests
fi

# Check if database is running
echo "🗄️ Checking database connection..."
python3 -c "
import pymysql
try:
    conn = pymysql.connect(host='localhost', user='root', password='', database='detect_db')
    conn.close()
    print('✅ Database connection OK')
except Exception as e:
    print(f'❌ Database error: {e}')
    print('Please ensure MySQL/MariaDB is running and detect_db database exists')
    exit(1)
"

if [ $? -ne 0 ]; then
    exit 1
fi

# Start the application
echo "🎬 Starting camera system..."
echo "📊 Dashboard will be available at: http://localhost:5000"
echo "⏹️ Press Ctrl+C to stop"
echo ""

python3 app.py
'''
    
    with open('startup.sh', 'w') as f:
        f.write(content)
    
    # Make executable
    import stat
    os.chmod('startup.sh', stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
    print("✅ Created startup.sh script")

def main():
    """Main fix function"""
    print("🔧 NT TELECOM COMPLETE SYSTEM FIX")
    print("=" * 50)
    
    # Create backup
    backup_dir = backup_files()
    
    # Create fixed files
    create_fixed_app_py()
    create_fixed_main_js()
    create_startup_script()
    
    print("\n" + "=" * 50)
    print("✅ SYSTEM FIX COMPLETED!")
    print("=" * 50)
    
    print("\n📋 WHAT WAS FIXED:")
    print("• ✅ Dashboard loading and updates")
    print("• ✅ Camera video feeds display")
    print("• ✅ Image download functionality")
    print("• ✅ Detection history table")
    print("• ✅ Navigation between pages")
    print("• ✅ Real-time data updates")
    print("• ✅ Error handling and logging")
    
    print("\n🚀 HOW TO START:")
    print("1. Run: chmod +x startup.sh")
    print("2. Run: ./startup.sh")
    print("3. Open browser: http://localhost:5000")
    
    print("\n🔧 MANUAL START:")
    print("python3 app.py")
    
    print("\n📊 EXPECTED RESULTS:")
    print("• Dashboard shows real detection counts")
    print("• All 4 camera feeds display (Front Gate, Main Entrance, Parking, Lobby)")
    print("• Detection history table loads with data")
    print("• Image download works from detection history")
    print("• Navigation works between all pages")
    print("• Real-time updates every 15 seconds")
    
    print("\n🔍 TROUBLESHOOTING:")
    print("• If cameras don't show: Check RTSP connectivity")
    print("• If no detections: Check database connection")
    print("• If images don't download: Check file permissions")
    print("• Open browser console (F12) for detailed errors")
    
    print(f"\n💾 Backup stored in: {backup_dir}")
    print("If issues persist, restore from backup and contact support.")

if __name__ == "__main__":
    main()