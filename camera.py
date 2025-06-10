# camera.py - Fixed CPU Half Precision Issue

import cv2
import numpy as np
import threading
import time
import os
import subprocess as sp
from datetime import datetime, timedelta
import queue
import hashlib
import torch
from ultralytics import YOLO
from utils import send_telegram_alert, send_telegram_photo
import gc
from collections import deque

class OptimizedCamera:
    def __init__(self, camera_id, rtsp_url, images_dir, settings):
        self.camera_id = camera_id
        self.safe_camera_id = camera_id.replace(' ', '_').replace('/', '_')
        self.rtsp_url = rtsp_url
        self.images_dir = images_dir
        self.settings = settings
        
        # Optimized detection settings
        self.detection_interval = settings.get('detection_interval', 180)
        self.confidence_threshold = settings.get('confidence_threshold', 0.6)
        
        # CPU Optimization settings
        self.process_every_n_frames = 8  # Increased from 6 to 8 for better CPU performance
        self.max_detection_resolution = 640
        self.display_resolution = (854, 480)
        self.detection_resolution = (320, 320)  # Even smaller for better CPU performance
        
        # Frame handling optimized for low CPU
        self.current_frame = None
        self.display_frame = None
        self.running = False
        self.lock = threading.Lock()
        
        # Minimal frame buffer
        self.frame_buffer = deque(maxlen=2)
        self.frame_count = 0
        
        # Enhanced person tracking
        self.detected_persons = {}
        self.detection_queue = queue.Queue(maxsize=3)  # Reduced queue size
        
        # Create directory
        self.today_dir = datetime.now().strftime("%Y%m%d")
        self.camera_image_dir = os.path.join(images_dir, self.today_dir, self.safe_camera_id)
        os.makedirs(self.camera_image_dir, exist_ok=True)
        
        # Performance tracking
        self.last_fps_time = time.time()
        self.fps_counter = 0
        self.current_fps = 0
        self.last_detection_time = 0
        
        # Shared model reference
        self.shared_model = None
    
    def start(self):
        """Start optimized camera threads"""
        if not self.running:
            self.running = True
            
            frame_thread = threading.Thread(target=self.update_frame, daemon=True)
            frame_thread.start()
            
            detect_thread = threading.Thread(target=self.detect_objects, daemon=True)
            detect_thread.start()
            
            process_thread = threading.Thread(target=self.process_detections, daemon=True)
            process_thread.start()
            
            print(f"📷 Started optimized camera: {self.camera_id}")
    
    def stop(self):
        """Stop camera"""
        self.running = False
        # Clear buffers
        self.frame_buffer.clear()
        self.current_frame = None
        self.display_frame = None
        gc.collect()
    
    def update_frame(self):
        """Optimized frame capture with lower CPU usage"""
        frame_width, frame_height = self.display_resolution
        frame_size = frame_width * frame_height * 3
        
        while self.running:
            try:
                # Optimized FFmpeg command
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-rtsp_transport', 'tcp',
                    '-i', self.rtsp_url,
                    '-loglevel', 'error',
                    '-an',
                    '-f', 'image2pipe',
                    '-pix_fmt', 'bgr24',
                    '-vcodec', 'rawvideo',
                    '-vf', f'scale={frame_width}:{frame_height}',
                    '-r', '12',  # Further reduced frame rate
                    '-probesize', '32',
                    '-analyzeduration', '0',
                    '-fflags', 'nobuffer+fastseek',
                    '-flags', 'low_delay',
                    '-threads', '1',  # Single thread for FFmpeg
                    '-'
                ]
                
                pipe = sp.Popen(ffmpeg_cmd, stdout=sp.PIPE, bufsize=frame_size*2)
                
                frame_skip_counter = 0
                
                while self.running:
                    raw_image = pipe.stdout.read(frame_size)
                    if len(raw_image) != frame_size:
                        print(f"Cannot read from {self.camera_id}")
                        break
                    
                    # Skip more frames to reduce CPU load
                    frame_skip_counter += 1
                    if frame_skip_counter % 3 != 0:  # Process every 3rd frame
                        continue
                    
                    frame = np.frombuffer(raw_image, dtype='uint8').reshape((frame_height, frame_width, 3))
                    
                    # FPS calculation
                    self.fps_counter += 1
                    current_time = time.time()
                    if current_time - self.last_fps_time >= 3.0:  # Update every 3 seconds
                        self.current_fps = self.fps_counter // 3
                        self.fps_counter = 0
                        self.last_fps_time = current_time
                    
                    with self.lock:
                        self.current_frame = frame
                        self.frame_buffer.append(frame.copy())
                    
                    time.sleep(0.08)  # Increased delay to reduce CPU
                
                pipe.terminate()
                pipe.wait()
                
            except Exception as e:
                print(f"Frame capture error {self.camera_id}: {e}")
                time.sleep(3)  # Longer wait on error
                gc.collect()
    
    def detect_objects(self):
        """Fixed CPU detection without half precision"""
        if self.shared_model is None:
            print(f"No shared model available for {self.camera_id}")
            return
        
        PERSON_CLASS_ID = 0
        last_process_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Increase detection interval for CPU saving
                if current_time - last_process_time < 3.0:  # Detect every 3 seconds
                    time.sleep(0.2)
                    continue
                
                # Update date folders
                self._update_date_folders()
                
                # Get frame for processing
                with self.lock:
                    if not self.frame_buffer:
                        time.sleep(0.2)
                        continue
                    process_frame = self.frame_buffer[-1].copy()
                
                # Resize frame for detection
                detect_frame = cv2.resize(process_frame, self.detection_resolution)
                
                # YOLO detection with CPU-optimized settings
                with torch.no_grad():
                    results = self.shared_model.predict(
                        source=detect_frame,
                        imgsz=320,  # Smaller input size
                        conf=self.confidence_threshold,
                        classes=[PERSON_CLASS_ID],
                        max_det=3,  # Limit detections even more
                        verbose=False,
                        half=False,  # FIXED: Disable half precision for CPU
                        device='cpu'
                    )
                
                result = results[0]
                boxes = result.boxes
                
                # Create display frame
                display_frame = process_frame.copy()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Scale factor for bounding boxes
                scale_x = process_frame.shape[1] / self.detection_resolution[0]
                scale_y = process_frame.shape[0] / self.detection_resolution[1]
                
                new_detections = []
                
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        # Scale coordinates back to display resolution
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        x1, x2 = int(x1 * scale_x), int(x2 * scale_x)
                        y1, y2 = int(y1 * scale_y), int(y2 * scale_y)
                        
                        conf = float(box.conf[0].item())
                        
                        # Simple tracking
                        center_x = (x1 + x2) // 2
                        center_y = (y1 + y2) // 2
                        area = (x2 - x1) * (y2 - y1)
                        
                        # Create hash for tracking
                        person_hash = f"{center_x//150}_{center_y//150}_{area//10000}"
                        
                        # Draw bounding box
                        color = (0, 255, 0) if conf > 0.7 else (0, 165, 255)
                        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(display_frame, f"Person: {conf:.0%}", 
                                  (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                        
                        # Check for new detection
                        if self._is_new_detection(person_hash, current_time):
                            detection_info = {
                                'camera_id': self.camera_id,
                                'timestamp': timestamp,
                                'confidence': round(conf * 100, 2),
                                'box': (x1, y1, x2, y2),
                                'frame': process_frame.copy(),
                                'person_hash': person_hash
                            }
                            new_detections.append(detection_info)
                
                # Add camera info overlay (simplified)
                cv2.rectangle(display_frame, (0, 0), (350, 50), (0, 0, 0), -1)
                cv2.putText(display_frame, f"{self.camera_id}", 
                           (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(display_frame, f"{timestamp[:19]} | FPS: {self.current_fps}", 
                           (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
                
                # Update display frame
                with self.lock:
                    self.display_frame = display_frame
                
                # Process new detections
                for detection in new_detections:
                    if not self.detection_queue.full():
                        try:
                            self.detection_queue.put(detection, block=False)
                        except queue.Full:
                            pass  # Skip if queue is full
                
                last_process_time = current_time
                
                # Memory cleanup
                if len(new_detections) > 0:
                    gc.collect()
                
                time.sleep(0.2)  # Increased sleep to reduce CPU load
                
            except Exception as e:
                print(f"Detection error {self.camera_id}: {e}")
                time.sleep(2)  # Longer wait on error
                gc.collect()
    
    def _is_new_detection(self, person_hash, current_time):
        """Optimized detection tracking"""
        if person_hash not in self.detected_persons:
            self.detected_persons[person_hash] = current_time
            return True
        
        last_time = self.detected_persons[person_hash]
        if current_time - last_time > self.detection_interval:
            self.detected_persons[person_hash] = current_time
            return True
        
        return False
    
    def process_detections(self):
        """Optimized detection processing"""
        while self.running:
            try:
                detection = self.detection_queue.get(timeout=2)
                
                # Generate filename
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"person_{timestamp_str}_{detection['confidence']:.0f}.jpg"
                image_path = os.path.join(self.camera_image_dir, filename)
                
                # Save image with lower quality
                cv2.imwrite(image_path, detection['frame'], 
                           [cv2.IMWRITE_JPEG_QUALITY, 75])
                
                # Create relative path
                date_str = datetime.now().strftime("%Y%m%d")
                rel_image_path = f"{date_str}/{self.safe_camera_id}/{filename}"
                
                # Send notifications in background
                threading.Thread(target=self._send_notifications, 
                               args=(detection, image_path), daemon=True).start()
                
                # Update app
                detection['image_path'] = rel_image_path
                self._update_detection_in_app(detection)
                
                self.detection_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Processing error: {e}")
                time.sleep(1)
    
    def _send_notifications(self, detection, image_path):
        """Send notifications in separate thread"""
        try:
            alert_message = f"""🚨 Person Detected

Camera: {detection['camera_id']}
Confidence: {detection['confidence']:.0f}%
Time: {detection['timestamp']}
"""
            send_telegram_alert(alert_message)
            
            time.sleep(1)  # Small delay between text and photo
            send_telegram_photo(image_path, f"Detection from {detection['camera_id']}")
        except Exception as e:
            print(f"Notification error: {e}")
    
    def _update_date_folders(self):
        """Update date folders if needed"""
        today = datetime.now().strftime("%Y%m%d")
        if today != self.today_dir:
            self.today_dir = today
            self.camera_image_dir = os.path.join(self.images_dir, today, self.safe_camera_id)
            os.makedirs(self.camera_image_dir, exist_ok=True)
            self.detected_persons.clear()
    
    def _update_detection_in_app(self, detection):
        """Update detection in Flask app"""
        import requests
        try:
            data = {k: v for k, v in detection.items() if k != 'frame'}
            requests.post('http://localhost:5000/update_detection', 
                         json=data, timeout=3)
        except Exception as e:
            print(f"App update error: {e}")
    
    def get_frame(self):
        """Get current frame for display"""
        with self.lock:
            if self.display_frame is not None:
                return self.display_frame
            elif self.current_frame is not None:
                return self.current_frame
        return None
    
    def get_jpeg(self):
        """Get JPEG encoded frame"""
        frame = self.get_frame()
        if frame is not None:
            # Lower quality JPEG for better performance
            ret, buffer = cv2.imencode('.jpg', frame, 
                                     [cv2.IMWRITE_JPEG_QUALITY, 70])  # Reduced quality
            if ret:
                return buffer.tobytes()
        return None
    
    def cleanup(self):
        """Cleanup resources"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # Keep only last hour
        
        self.detected_persons = {
            h: t for h, t in self.detected_persons.items() 
            if t > cutoff_time
        }


class OptimizedCameraSystem:
    def __init__(self, camera_urls, images_dir, settings):
        self.cameras = {}
        self.images_dir = images_dir
        self.settings = settings
        self.start_time = time.time()
        
        # Initialize shared model once
        self.shared_model = self._load_optimized_model()
        
        # Create camera instances
        for camera_id, url in camera_urls.items():
            camera = OptimizedCamera(camera_id, url, images_dir, settings)
            camera.shared_model = self.shared_model
            self.cameras[camera_id] = camera
        
        # Start periodic cleanup
        threading.Thread(target=self._periodic_cleanup, daemon=True).start()
    
    def _load_optimized_model(self):
        """Load optimized YOLO model for CPU"""
        try:
            print("🤖 Loading CPU-optimized YOLO model...")
            
            # Try different models
            model_options = [
                "yolov8n.pt",      # Fastest for CPU
                "yolov5n.pt",      # Alternative
                "yolov5s.pt"       # Better accuracy
            ]
            
            for model_name in model_options:
                try:
                    model = YOLO(model_name)
                    
                    # Optimize for CPU
                    model.model.eval()
                    model.to('cpu')
                    
                    # Test the model to ensure it works
                    test_img = np.zeros((320, 320, 3), dtype=np.uint8)
                    with torch.no_grad():
                        results = model.predict(
                            source=test_img,
                            verbose=False,
                            half=False,  # NO half precision for CPU
                            device='cpu'
                        )
                    
                    print(f"✅ Successfully loaded: {model_name}")
                    return model
                    
                except Exception as e:
                    print(f"Failed to load {model_name}: {e}")
                    continue
            
            print("❌ Failed to load any YOLO model")
            return None
            
        except Exception as e:
            print(f"Model loading error: {e}")
            return None
    
    def start_all(self):
        """Start all cameras"""
        if self.shared_model is None:
            print("❌ Cannot start cameras - no model loaded")
            return
            
        for camera_id, camera in self.cameras.items():
            camera.start()
            time.sleep(0.5)  # Stagger startup
        print(f"✅ Started {len(self.cameras)} optimized cameras")
    
    def stop_all(self):
        """Stop all cameras"""
        for camera in self.cameras.values():
            camera.stop()
        
        if self.shared_model:
            del self.shared_model
        
        gc.collect()
        print("🛑 Stopped all cameras")
    
    def get_jpeg(self, camera_id):
        """Get JPEG from specific camera"""
        if camera_id in self.cameras:
            return self.cameras[camera_id].get_jpeg()
        return None
    
    def _periodic_cleanup(self):
        """Periodic cleanup"""
        while True:
            try:
                time.sleep(600)  # Every 10 minutes
                
                for camera in self.cameras.values():
                    camera.cleanup()
                
                # Force garbage collection
                gc.collect()
                
                print("🧹 Performed periodic cleanup")
                
            except Exception as e:
                print(f"Cleanup error: {e}")
                time.sleep(120)  # Wait 2 minutes on error